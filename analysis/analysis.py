#!/usr/bin/env python3
"""Reproducible corpus analysis for the PLC 51 abstract.

The script reads recent Git commit subject lines from a fixed set of public
repositories and identifies clause-initial members of curated verb paradigms.
The paradigms are deliberately conservative: only forms whose orthography
unambiguously distinguishes BASE, PAST, 3SG, and PROG are included.
"""

from __future__ import annotations

import csv
import math
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT / "data" / "repos"
REPOSITORIES = [
    "cpython",
    "react",
    "django",
    "go",
    "node",
    "pytorch",
    "flask",
    "requests",
    "numpy",
    "pandas",
    "fastapi",
    "vue",
    "svelte",
    "httpx",
]

# (lemma, base, past/participle, 3sg, progressive)
# Avoid syncretic paradigms such as set/set and forms with likely noun readings
# such as release/released.
PARADIGMS = [
    ("add", "add", "added", "adds", "adding"),
    ("adjust", "adjust", "adjusted", "adjusts", "adjusting"),
    ("align", "align", "aligned", "aligns", "aligning"),
    ("allow", "allow", "allowed", "allows", "allowing"),
    ("avoid", "avoid", "avoided", "avoids", "avoiding"),
    ("bump", "bump", "bumped", "bumps", "bumping"),
    ("change", "change", "changed", "changes", "changing"),
    ("clarify", "clarify", "clarified", "clarifies", "clarifying"),
    ("clean", "clean", "cleaned", "cleans", "cleaning"),
    ("correct", "correct", "corrected", "corrects", "correcting"),
    ("deprecate", "deprecate", "deprecated", "deprecates", "deprecating"),
    ("disable", "disable", "disabled", "disables", "disabling"),
    ("document", "document", "documented", "documents", "documenting"),
    ("drop", "drop", "dropped", "drops", "dropping"),
    ("enable", "enable", "enabled", "enables", "enabling"),
    ("ensure", "ensure", "ensured", "ensures", "ensuring"),
    ("expose", "expose", "exposed", "exposes", "exposing"),
    ("fix", "fix", "fixed", "fixes", "fixing"),
    ("handle", "handle", "handled", "handles", "handling"),
    ("implement", "implement", "implemented", "implements", "implementing"),
    ("improve", "improve", "improved", "improves", "improving"),
    ("increase", "increase", "increased", "increases", "increasing"),
    ("introduce", "introduce", "introduced", "introduces", "introducing"),
    ("mark", "mark", "marked", "marks", "marking"),
    ("move", "move", "moved", "moves", "moving"),
    ("optimize", "optimize", "optimized", "optimizes", "optimizing"),
    ("prevent", "prevent", "prevented", "prevents", "preventing"),
    ("reduce", "reduce", "reduced", "reduces", "reducing"),
    ("refactor", "refactor", "refactored", "refactors", "refactoring"),
    ("remove", "remove", "removed", "removes", "removing"),
    ("rename", "rename", "renamed", "renames", "renaming"),
    ("replace", "replace", "replaced", "replaces", "replacing"),
    ("restore", "restore", "restored", "restores", "restoring"),
    ("return", "return", "returned", "returns", "returning"),
    ("revert", "revert", "reverted", "reverts", "reverting"),
    ("simplify", "simplify", "simplified", "simplifies", "simplifying"),
    ("support", "support", "supported", "supports", "supporting"),
    ("switch", "switch", "switched", "switches", "switching"),
    ("update", "update", "updated", "updates", "updating"),
    ("upgrade", "upgrade", "upgraded", "upgrades", "upgrading"),
]

FORM_INDEX: dict[str, tuple[str, str]] = {}
for lemma, base, past, third, prog in PARADIGMS:
    for form, category in [(base, "BASE"), (past, "PAST"), (third, "3SG"), (prog, "PROG")]:
        FORM_INDEX[form] = (lemma, category)

FIRST_WORD = re.compile(r"^[^A-Za-z]*([A-Za-z]+)")
EXCLUDE = re.compile(r"^(merge|revert\s+\"|cherry-pick|backport)\b", re.I)
LEADING_TAG = re.compile(r"^(?:\[[^\]]+\]\s*)+")
SCOPE_PREFIX = re.compile(r"^([^:]{1,60}):\s+(.+)$")


def subjects(repo: str, limit: int = 1000) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT / repo), "log", f"-{limit}", "--no-merges", "--format=%s"],
        check=True,
        text=True,
        capture_output=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def initial_form(subject: str) -> str | None:
    """Return the first clausal word after conventional scope labels.

    Many projects prefix subjects with a subsystem (``net/http: fix ...``) or
    a bracketed review tag. We strip one such metadata field only when the text
    following it begins with a member of our verb inventory; this prevents a
    lexical colon such as ``Fix: ...`` from being silently discarded.
    """
    text = LEADING_TAG.sub("", subject).strip()
    match = FIRST_WORD.search(text)
    if match and match.group(1).lower() in FORM_INDEX:
        return match.group(1).lower()
    scope = SCOPE_PREFIX.match(text)
    if scope:
        after = scope.group(2)
        match = FIRST_WORD.search(after)
        if match and match.group(1).lower() in FORM_INDEX:
            return match.group(1).lower()
    return None


def entropy(counts: Counter[str]) -> float:
    total = sum(counts.values())
    return -sum((n / total) * math.log2(n / total) for n in counts.values() if n)


rows: list[dict[str, str]] = []
repo_totals: Counter[str] = Counter()

for repo in REPOSITORIES:
    for subject in subjects(repo):
        repo_totals[repo] += 1
        if EXCLUDE.search(subject):
            continue
        form = initial_form(subject)
        if not form:
            continue
        lemma, category = FORM_INDEX[form]
        rows.append({
            "repository": repo,
            "subject": subject,
            "first_form": form,
            "lemma": lemma,
            "category": category,
        })

out_dir = ROOT / "results"
out_dir.mkdir(exist_ok=True)
with (out_dir / "coded_commits.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

overall = Counter(row["category"] for row in rows)
by_repo: dict[str, Counter[str]] = defaultdict(Counter)
by_lemma: dict[str, Counter[str]] = defaultdict(Counter)
for row in rows:
    by_repo[row["repository"]][row["category"]] += 1
    by_lemma[row["lemma"]][row["category"]] += 1

# Mutual information between repository and BASE/PAST choice. This measures
# community conventionalization without assuming a particular regression link.
bp = [row for row in rows if row["category"] in {"BASE", "PAST"}]
joint = Counter((row["repository"], row["category"]) for row in bp)
repo_marginal = Counter(row["repository"] for row in bp)
cat_marginal = Counter(row["category"] for row in bp)
n_bp = len(bp)
mi = 0.0
for (repo, cat), n in joint.items():
    p_joint = n / n_bp
    mi += p_joint * math.log2(p_joint / ((repo_marginal[repo] / n_bp) * (cat_marginal[cat] / n_bp)))

summary_lines = [
    f"total_subjects={sum(repo_totals.values())}",
    f"coded_initial_verbs={len(rows)}",
    "overall=" + ",".join(f"{k}:{overall[k]}" for k in ["BASE", "PAST", "3SG", "PROG"]),
    f"base_past_mutual_information_bits={mi:.4f}",
    f"base_past_entropy_bits={entropy(Counter(row['category'] for row in bp)):.4f}",
]
for repo in REPOSITORIES:
    c = by_repo[repo]
    denom = c["BASE"] + c["PAST"]
    share = c["BASE"] / denom if denom else float("nan")
    summary_lines.append(
        f"repo={repo}\ttotal={repo_totals[repo]}\tcoded={sum(c.values())}\t"
        f"base={c['BASE']}\tpast={c['PAST']}\t3sg={c['3SG']}\tprog={c['PROG']}\tbase_share={share:.3f}"
    )

top_lemmas = sorted(by_lemma.items(), key=lambda item: sum(item[1].values()), reverse=True)[:15]
for lemma, c in top_lemmas:
    summary_lines.append(
        f"lemma={lemma}\tbase={c['BASE']}\tpast={c['PAST']}\t3sg={c['3SG']}\tprog={c['PROG']}"
    )

(out_dir / "summary.txt").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
print("\n".join(summary_lines))
