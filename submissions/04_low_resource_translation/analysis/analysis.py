#!/usr/bin/env python3
"""Audit transliteration gains in Cherokee-English translation-memory retrieval.

The public ChrEn parquet files are expected under data/chr_en/parallel.
The analysis compares raw Cherokee-syllabary character retrieval, a lossless
Unicode-name romanization, and length-matched shuffled romanization controls.
"""

from __future__ import annotations

import json
import random
import unicodedata as ud
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "chr_en" / "parallel"
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)


def load(split: str) -> tuple[list[str], list[str]]:
    frame = pd.read_parquet(DATA / f"{split}-00000-of-00001.parquet")
    pairs = frame["sentence_pair"].tolist()
    return [x["chr"] for x in pairs], [x["en"] for x in pairs]


def cherokee_label(char: str) -> str | None:
    name = ud.name(char, "")
    if name.startswith("CHEROKEE LETTER "):
        return name.removeprefix("CHEROKEE LETTER ").lower()
    if name.startswith("CHEROKEE SMALL LETTER "):
        return name.removeprefix("CHEROKEE SMALL LETTER ").lower()
    return None


def make_mapping(texts: list[str]) -> dict[str, str]:
    return {
        char: label
        for char in sorted(set("".join(texts)))
        if (label := cherokee_label(char)) is not None
    }


def convert(text: str, mapping: dict[str, str] | None) -> str:
    if mapping is None:
        return text
    return "".join(mapping.get(char, char.lower()) for char in text)


def shuffled_mapping(mapping: dict[str, str], seed: int) -> dict[str, str]:
    """Permute labels within length classes, preserving expansion exactly."""
    rng = random.Random(seed)
    groups: dict[int, list[str]] = defaultdict(list)
    for char, label in mapping.items():
        groups[len(label)].append(char)
    shuffled: dict[str, str] = {}
    for chars in groups.values():
        labels = [mapping[char] for char in chars]
        rng.shuffle(labels)
        shuffled.update(zip(chars, labels))
    return shuffled


def ngram_stats(hyp: str, ref: str, order: int) -> tuple[int, int, int]:
    hyp = " ".join(hyp.lower().split())
    ref = " ".join(ref.lower().split())
    hyp_counts = Counter(hyp[i : i + order] for i in range(max(0, len(hyp) - order + 1)))
    ref_counts = Counter(ref[i : i + order] for i in range(max(0, len(ref) - order + 1)))
    return sum((hyp_counts & ref_counts).values()), sum(hyp_counts.values()), sum(ref_counts.values())


def sentence_stats(hyps: list[str], refs: list[str], max_order: int = 6) -> np.ndarray:
    return np.array(
        [[ngram_stats(hyp, ref, order) for order in range(1, max_order + 1)] for hyp, ref in zip(hyps, refs)],
        dtype=np.int64,
    )


def chrf2_from_stats(stats: np.ndarray, indices: np.ndarray | None = None) -> float:
    selected = stats if indices is None else stats[indices]
    totals = selected.sum(axis=0)
    scores = []
    for matches, hyp_total, ref_total in totals:
        precision = matches / hyp_total if hyp_total else 0.0
        recall = matches / ref_total if ref_total else 0.0
        scores.append(5 * precision * recall / (4 * precision + recall) if precision + recall else 0.0)
    return 100 * float(np.mean(scores))


def retrieve(
    train_x: list[str],
    train_y: list[str],
    query_x: list[str],
    mapping: dict[str, str] | None,
    ngrams: tuple[int, int],
) -> tuple[list[str], np.ndarray, np.ndarray]:
    vectorizer = TfidfVectorizer(
        analyzer="char",
        ngram_range=ngrams,
        min_df=2,
        sublinear_tf=True,
        norm="l2",
        max_features=250_000,
    )
    train_matrix = vectorizer.fit_transform([convert(text, mapping) for text in train_x])
    query_matrix = vectorizer.transform([convert(text, mapping) for text in query_x])
    neighbors = NearestNeighbors(n_neighbors=1, metric="cosine", algorithm="brute", n_jobs=-1)
    neighbors.fit(train_matrix)
    distance, index = neighbors.kneighbors(query_matrix)
    indices = index[:, 0]
    return [train_y[i] for i in indices], indices, 1 - distance[:, 0]


train_x, train_y = load("train")
dev_x, dev_y = load("dev")
test_x, test_y = load("test")
out_test_x, out_test_y = load("out_test")
roman = make_mapping(train_x + dev_x + test_x + out_test_x)

grid = [(1, 4), (1, 6), (2, 5), (2, 6), (2, 8)]
dev_scores: dict[str, dict[str, float]] = {"raw": {}, "romanized": {}}
for label, mapping in [("raw", None), ("romanized", roman)]:
    for ngrams in grid:
        hypotheses, _, _ = retrieve(train_x, train_y, dev_x, mapping, ngrams)
        dev_scores[label][f"{ngrams[0]}-{ngrams[1]}"] = chrf2_from_stats(sentence_stats(hypotheses, dev_y))

best_raw = max(dev_scores["raw"], key=dev_scores["raw"].get)
best_roman = max(dev_scores["romanized"], key=dev_scores["romanized"].get)
raw_range = tuple(map(int, best_raw.split("-")))
roman_range = tuple(map(int, best_roman.split("-")))

systems: dict[str, dict[str, object]] = {}
predictions: dict[str, list[str]] = {}
for split, query_x, refs in [("test", test_x, test_y), ("out_test", out_test_x, out_test_y)]:
    for label, mapping, ngrams in [
        ("raw", None, raw_range),
        ("romanized", roman, roman_range),
    ]:
        hypotheses, indices, similarities = retrieve(train_x, train_y, query_x, mapping, ngrams)
        stats = sentence_stats(hypotheses, refs)
        systems[f"{label}_{split}"] = {
            "chrf2": chrf2_from_stats(stats),
            "mean_source_similarity": float(similarities.mean()),
            "mean_hypothesis_length": float(np.mean([len(x) for x in hypotheses])),
        }
        if split == "test":
            predictions[label] = hypotheses

# Paired bootstrap for the raw-to-romanized test difference.
raw_stats = sentence_stats(predictions["raw"], test_y)
roman_stats = sentence_stats(predictions["romanized"], test_y)
rng = np.random.default_rng(20261105)
differences = []
for _ in range(2_000):
    sample = rng.integers(0, len(test_y), size=len(test_y))
    differences.append(chrf2_from_stats(roman_stats, sample) - chrf2_from_stats(raw_stats, sample))

# Label-permutation control: keep every romanized label's length and inventory,
# but destroy its association with a Cherokee syllabary symbol.
permutation_scores = []
for seed in range(20):
    shuffled = shuffled_mapping(roman, seed)
    hypotheses, _, _ = retrieve(train_x, train_y, test_x, shuffled, roman_range)
    permutation_scores.append(chrf2_from_stats(sentence_stats(hypotheses, test_y)))

roman_score = float(systems["romanized_test"]["chrf2"])
results = {
    "dataset_sizes": {
        "train": len(train_x),
        "dev": len(dev_x),
        "test": len(test_x),
        "out_test": len(out_test_x),
    },
    "romanization_symbols": len(roman),
    "development_grid": dev_scores,
    "selected_ngrams": {"raw": raw_range, "romanized": roman_range},
    "systems": systems,
    "test_difference_roman_minus_raw": roman_score - float(systems["raw_test"]["chrf2"]),
    "bootstrap_95_percent_interval": [float(np.quantile(differences, 0.025)), float(np.quantile(differences, 0.975))],
    "bootstrap_probability_difference_le_zero": float(np.mean(np.array(differences) <= 0)),
    "shuffled_control": {
        "runs": len(permutation_scores),
        "mean": float(np.mean(permutation_scores)),
        "standard_deviation": float(np.std(permutation_scores, ddof=1)),
        "minimum": float(np.min(permutation_scores)),
        "maximum": float(np.max(permutation_scores)),
        "romanized_percentile": float(np.mean(np.array(permutation_scores) < roman_score)),
        "scores": permutation_scores,
    },
}
(OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

pd.DataFrame(
    {
        "cherokee": test_x,
        "reference_english": test_y,
        "raw_retrieval": predictions["raw"],
        "romanized_retrieval": predictions["romanized"],
    }
).to_csv(OUT / "test_predictions.csv", index=False)

print(json.dumps(results, indent=2))
