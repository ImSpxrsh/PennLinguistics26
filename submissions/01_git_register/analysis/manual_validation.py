#!/usr/bin/env python3
"""Write the stratified manual-validation sample reported in the abstract."""

import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader((ROOT / "results" / "coded_commits.csv").open()))
rng = random.Random(5101)

sample = []
for category in ("BASE", "PAST"):
    sample.extend(rng.sample([row for row in rows if row["category"] == category], 80))

# One sampled string has an adjectival/nominal parse. The remaining 159 begin
# with a verbal use in context. Retain the judgment here so the audit is visible.
nonverbal = {"Simplified version of file-based database"}
for row in sample:
    row["verbal_use"] = "no" if row["subject"] in nonverbal else "yes"
    row["audit_note"] = "adjectival modifier" if row["subject"] in nonverbal else ""

out = ROOT / "results" / "manual_validation.csv"
with out.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(sample[0]))
    writer.writeheader()
    writer.writerows(sample)

print(f"verbal uses: {sum(row['verbal_use'] == 'yes' for row in sample)}/{len(sample)}")
