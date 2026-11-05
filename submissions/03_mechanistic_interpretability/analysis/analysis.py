#!/usr/bin/env python3
"""Layerwise diagnostic and causal analysis of English agreement in DistilGPT-2."""

from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, cross_val_score
from transformers import AutoModelForCausalLM, AutoTokenizer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS = PROJECT_ROOT / "results"
MODEL_NAME = "distilgpt2"
SEED = 51

NOUNS = [
    ("key", "keys", "cabinet", "cabinets"),
    ("report", "reports", "editor", "editors"),
    ("photo", "photos", "journalist", "journalists"),
    ("label", "labels", "container", "containers"),
    ("message", "messages", "student", "students"),
    ("article", "articles", "reviewer", "reviewers"),
    ("doctor", "doctors", "patient", "patients"),
    ("teacher", "teachers", "principal", "principals"),
    ("pilot", "pilots", "mechanic", "mechanics"),
    ("recipe", "recipes", "chef", "chefs"),
]


def make_items() -> pd.DataFrame:
    rows = []
    for group, (subj_s, subj_p, attr_s, attr_p) in enumerate(NOUNS):
        for subj_num, subj in [(0, subj_s), (1, subj_p)]:
            for attr_num, attr in [(0, attr_s), (1, attr_p)]:
                rows.append({
                    "prefix": f"The {subj} near the {attr}",
                    "structure": "PP",
                    "subject_plural": subj_num,
                    "attractor_plural": attr_num,
                    "lexical_group": group,
                })
                rows.append({
                    "prefix": f"The {subj} that the {attr} can describe",
                    "structure": "RC",
                    "subject_plural": subj_num,
                    "attractor_plural": attr_num,
                    "lexical_group": group,
                })
    return pd.DataFrame(rows)


def margin_from_logits(logits: torch.Tensor, is_id: int, are_id: int) -> np.ndarray:
    return (logits[:, are_id] - logits[:, is_id]).detach().cpu().numpy()


def main() -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    model.eval()

    is_tokens = tokenizer.encode(" is", add_special_tokens=False)
    are_tokens = tokenizer.encode(" are", add_special_tokens=False)
    assert len(is_tokens) == len(are_tokens) == 1
    is_id, are_id = is_tokens[0], are_tokens[0]

    items = make_items()
    encoded = tokenizer(
        items.prefix.tolist(), return_tensors="pt", padding=True, add_special_tokens=False
    )
    final_pos = encoded.attention_mask.sum(dim=1) - 1
    batch_index = torch.arange(len(items))

    with torch.inference_mode():
        base = model(**encoded, output_hidden_states=True)
    next_logits = base.logits[batch_index, final_pos]
    signed_margin = margin_from_logits(next_logits, is_id, are_id)
    correct_sign = np.where(items.subject_plural.to_numpy() == 1, 1.0, -1.0)
    correct_margin = signed_margin * correct_sign

    items["are_minus_is"] = signed_margin
    items["correct_margin"] = correct_margin
    items["correct"] = correct_margin > 0
    items["congruent"] = items.subject_plural == items.attractor_plural

    hidden = []
    for layer_h in base.hidden_states:
        hidden.append(layer_h[batch_index, final_pos].detach().cpu().numpy())

    groups = items.lexical_group.to_numpy()
    subject_y = items.subject_plural.to_numpy()
    attractor_y = items.attractor_plural.to_numpy()
    cv = GroupKFold(n_splits=5)
    layer_rows = []

    # Hidden state 0 is the embedding output; states 1..6 follow transformer blocks.
    for state_idx, X in enumerate(hidden):
        subject_probe = LogisticRegression(max_iter=3000, random_state=SEED)
        attractor_probe = LogisticRegression(max_iter=3000, random_state=SEED)
        subject_cv = cross_val_score(subject_probe, X, subject_y, cv=cv, groups=groups).mean()
        attractor_cv = cross_val_score(attractor_probe, X, attractor_y, cv=cv, groups=groups).mean()

        if state_idx == 0:
            causal_drop = np.nan
            attractor_drop = np.nan
            random_drop = np.nan
            erased_accuracy = np.nan
            erased_incongruent_accuracy = np.nan
            attractor_erased_accuracy = np.nan
            attractor_erased_incongruent_accuracy = np.nan
            random_accuracy = np.nan
        else:
            subject_probe.fit(X, subject_y)
            direction = subject_probe.coef_[0]
            direction = direction / np.linalg.norm(direction)
            attractor_probe.fit(X, attractor_y)
            attractor_direction = attractor_probe.coef_[0]
            attractor_direction = attractor_direction / np.linalg.norm(attractor_direction)
            center = X.mean(axis=0)
            direction_t = torch.tensor(direction, dtype=next(model.parameters()).dtype)
            attractor_direction_t = torch.tensor(
                attractor_direction, dtype=next(model.parameters()).dtype
            )
            center_t = torch.tensor(center, dtype=next(model.parameters()).dtype)

            def erase_direction(_module, _inputs, output):
                hs = output[0] if isinstance(output, tuple) else output
                hs = hs.clone()
                selected = hs[batch_index, final_pos]
                projection = ((selected - center_t) @ direction_t).unsqueeze(1) * direction_t
                hs[batch_index, final_pos] = selected - projection
                return (hs,) + output[1:] if isinstance(output, tuple) else hs

            handle = model.transformer.h[state_idx - 1].register_forward_hook(erase_direction)
            with torch.inference_mode():
                erased = model(**encoded).logits[batch_index, final_pos]
            handle.remove()
            erased_correct = margin_from_logits(erased, is_id, are_id) * correct_sign
            causal_drop = float(np.mean(correct_margin - erased_correct))
            erased_accuracy = float(np.mean(erased_correct > 0))
            erased_incongruent_accuracy = float(
                np.mean(erased_correct[~items.congruent.to_numpy()] > 0)
            )
            if state_idx == len(hidden) - 1:
                items["final_erased_correct_margin"] = erased_correct
                items["final_erased_correct"] = erased_correct > 0

            def erase_attractor(_module, _inputs, output):
                hs = output[0] if isinstance(output, tuple) else output
                hs = hs.clone()
                selected = hs[batch_index, final_pos]
                projection = (
                    ((selected - center_t) @ attractor_direction_t).unsqueeze(1)
                    * attractor_direction_t
                )
                hs[batch_index, final_pos] = selected - projection
                return (hs,) + output[1:] if isinstance(output, tuple) else hs

            handle = model.transformer.h[state_idx - 1].register_forward_hook(erase_attractor)
            with torch.inference_mode():
                attractor_erased = model(**encoded).logits[batch_index, final_pos]
            handle.remove()
            attractor_erased_correct = (
                margin_from_logits(attractor_erased, is_id, are_id) * correct_sign
            )
            attractor_drop = float(np.mean(correct_margin - attractor_erased_correct))
            attractor_erased_accuracy = float(np.mean(attractor_erased_correct > 0))
            attractor_erased_incongruent_accuracy = float(
                np.mean(attractor_erased_correct[~items.congruent.to_numpy()] > 0)
            )
            if state_idx == len(hidden) - 1:
                items["final_attractor_erased_correct_margin"] = attractor_erased_correct
                items["final_attractor_erased_correct"] = attractor_erased_correct > 0

            random_drops = []
            random_accuracies = []
            for control_seed in range(10):
                rng = np.random.default_rng(SEED + control_seed)
                random_direction = rng.normal(size=direction.shape)
                random_direction /= np.linalg.norm(random_direction)
                random_t = torch.tensor(random_direction, dtype=direction_t.dtype)

                def erase_random(_module, _inputs, output, vector=random_t):
                    hs = output[0] if isinstance(output, tuple) else output
                    hs = hs.clone()
                    selected = hs[batch_index, final_pos]
                    projection = ((selected - center_t) @ vector).unsqueeze(1) * vector
                    hs[batch_index, final_pos] = selected - projection
                    return (hs,) + output[1:] if isinstance(output, tuple) else hs

                handle = model.transformer.h[state_idx - 1].register_forward_hook(erase_random)
                with torch.inference_mode():
                    random_logits = model(**encoded).logits[batch_index, final_pos]
                handle.remove()
                random_correct = margin_from_logits(random_logits, is_id, are_id) * correct_sign
                random_drops.append(float(np.mean(correct_margin - random_correct)))
                random_accuracies.append(float(np.mean(random_correct > 0)))
            random_drop = float(np.mean(random_drops))
            random_accuracy = float(np.mean(random_accuracies))

        layer_rows.append({
            "state": state_idx,
            "subject_number_cv_accuracy": float(subject_cv),
            "attractor_number_cv_accuracy": float(attractor_cv),
            "subject_direction_margin_drop": causal_drop,
            "attractor_direction_margin_drop": attractor_drop,
            "random_direction_margin_drop": random_drop,
            "subject_direction_accuracy": erased_accuracy,
            "subject_direction_incongruent_accuracy": erased_incongruent_accuracy,
            "attractor_direction_accuracy": attractor_erased_accuracy,
            "attractor_direction_incongruent_accuracy": attractor_erased_incongruent_accuracy,
            "random_direction_accuracy": random_accuracy,
        })

    layers = pd.DataFrame(layer_rows)
    final_difference = (
        items.correct_margin.to_numpy() - items.final_erased_correct_margin.to_numpy()
    )
    bootstrap_rng = np.random.default_rng(SEED)
    bootstrap_means = np.array([
        bootstrap_rng.choice(final_difference, size=len(final_difference), replace=True).mean()
        for _ in range(10_000)
    ])

    summary = {
        "model": MODEL_NAME,
        "n_items": int(len(items)),
        "overall_accuracy": float(items.correct.mean()),
        "congruent_accuracy": float(items.loc[items.congruent, "correct"].mean()),
        "incongruent_accuracy": float(items.loc[~items.congruent, "correct"].mean()),
        "pp_accuracy": float(items.loc[items.structure == "PP", "correct"].mean()),
        "rc_accuracy": float(items.loc[items.structure == "RC", "correct"].mean()),
        "best_subject_probe_state": int(layers.subject_number_cv_accuracy.idxmax()),
        "best_subject_probe_accuracy": float(layers.subject_number_cv_accuracy.max()),
        "best_attractor_probe_accuracy": float(layers.attractor_number_cv_accuracy.max()),
        "largest_causal_drop_state": int(layers.subject_direction_margin_drop.idxmax()),
        "largest_causal_margin_drop": float(layers.subject_direction_margin_drop.max()),
        "accuracy_after_final_subject_erasure": float(
            layers.loc[layers.state == 6, "subject_direction_accuracy"].iloc[0]
        ),
        "incongruent_accuracy_after_final_subject_erasure": float(
            layers.loc[layers.state == 6, "subject_direction_incongruent_accuracy"].iloc[0]
        ),
        "final_attractor_direction_margin_drop": float(
            layers.loc[layers.state == 6, "attractor_direction_margin_drop"].iloc[0]
        ),
        "accuracy_after_final_attractor_erasure": float(
            layers.loc[layers.state == 6, "attractor_direction_accuracy"].iloc[0]
        ),
        "incongruent_accuracy_after_final_attractor_erasure": float(
            layers.loc[layers.state == 6, "attractor_direction_incongruent_accuracy"].iloc[0]
        ),
        "mean_random_direction_accuracy_at_final": float(
            layers.loc[layers.state == 6, "random_direction_accuracy"].iloc[0]
        ),
        "final_margin_drop_bootstrap_ci95": [
            float(np.quantile(bootstrap_means, 0.025)),
            float(np.quantile(bootstrap_means, 0.975)),
        ],
    }

    RESULTS.mkdir(exist_ok=True)
    items.to_csv(RESULTS / "items.csv", index=False)
    layers.to_csv(RESULTS / "layer_results.csv", index=False)
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print(layers.to_string(index=False))


if __name__ == "__main__":
    main()
