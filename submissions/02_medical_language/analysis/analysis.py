#!/usr/bin/env python3
"""Measure line-break-sensitive negation scope in trial eligibility criteria.

The corpus is a fixed four-domain snapshot from the public ClinicalTrials.gov
API v2.  The analysis compares a line-aware representation with a common
punctuation-only normalization that replaces newlines with spaces.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "studies.jsonl"
RESULTS = ROOT / "results"

DOMAINS = {
    "oncology": "cancer",
    "cardiology": "heart disease",
    "diabetes": "diabetes",
    "psychiatry": "depression",
}

API = "https://clinicaltrials.gov/api/v2/studies"
HEADING = re.compile(
    r"^(?:criteria:\s*)?(?:key\s+)?(inclusion|exclusion)\s+criteria\s*:? *$",
    re.I,
)
BULLET = re.compile(r"^\s*(?:[*•●◦▪-]|\(?\d+[.)])\s+")
TERMINAL = re.compile(r"[.!?;:]\s*[\])}\"']*\s*$")
WORD = re.compile(r"\b[\w'-]+\b", re.UNICODE)
NEGATION = re.compile(
    r"\b(?:no|not|without|never|neither|cannot|can't|must\s+not|may\s+not|"
    r"absence\s+of|free\s+of|negative\s+for)\b",
    re.I,
)


def fetch(limit: int) -> None:
    DATA.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for domain, query in DOMAINS.items():
        params = {
            "query.cond": query,
            "filter.overallStatus": "RECRUITING",
            "pageSize": str(limit),
            "fields": "NCTId,EligibilityModule",
            "sort": "LastUpdatePostDate:desc",
            "format": "json",
        }
        url = API + "?" + urllib.parse.urlencode(params)
        response = subprocess.run(
            ["curl", "-L", "--fail", "--silent", "--show-error", url],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(response.stdout)
        for study in payload.get("studies", []):
            protocol = study.get("protocolSection", {})
            nct_id = protocol.get("identificationModule", {}).get("nctId")
            criteria = protocol.get("eligibilityModule", {}).get("eligibilityCriteria")
            if not nct_id or not criteria or nct_id in seen:
                continue
            seen.add(nct_id)
            rows.append({"domain": domain, "nct_id": nct_id, "criteria": criteria})
    with DATA.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} studies to {DATA}")


def criteria_lines(text: str) -> list[dict[str, object]]:
    section = "unknown"
    units: list[dict[str, object]] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        is_bullet = bool(BULLET.match(stripped))
        content = BULLET.sub("", stripped).strip()
        heading = HEADING.match(content)
        if heading:
            section = heading.group(1).lower()
            continue
        if not content:
            continue
        if is_bullet:
            units.append({"section": section, "text": content})
        elif units:
            # Wrapped prose inside a bullet is continuation, not a new criterion.
            units[-1]["text"] = str(units[-1]["text"]) + " " + content

    for unit in units:
        content = str(unit["text"])
        unit.update(
            {
                "bullet": True,
                "negated": bool(NEGATION.search(content)),
                "terminal": bool(TERMINAL.search(content)),
                "words": len(WORD.findall(content)),
            }
        )
    return units


def analyze() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    studies = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line]
    aggregate = Counter()
    domain_counts: dict[str, Counter] = defaultdict(Counter)
    events: list[dict[str, object]] = []

    for study in studies:
        lines = criteria_lines(study["criteria"])
        aggregate["studies"] += 1
        aggregate["studies_with_structured_units"] += int(bool(lines))
        aggregate["criteria_lines"] += len(lines)
        aggregate["bullet_lines"] += sum(bool(line["bullet"]) for line in lines)
        domain = study["domain"]
        domain_counts[domain]["studies"] += 1
        domain_counts[domain]["studies_with_structured_units"] += int(bool(lines))
        domain_counts[domain]["criteria_lines"] += len(lines)
        domain_counts[domain]["bullet_lines"] += sum(bool(line["bullet"]) for line in lines)

        for index, line in enumerate(lines):
            if not line["negated"]:
                continue
            aggregate["negated_lines"] += 1
            domain_counts[domain]["negated_lines"] += 1
            if line["terminal"] or index + 1 >= len(lines):
                continue
            if lines[index + 1]["section"] != line["section"]:
                continue

            crossed = 0
            extra_words = 0
            next_examples: list[str] = []
            for following in lines[index + 1 :]:
                if following["section"] != line["section"]:
                    break
                crossed += 1
                extra_words += int(following["words"])
                if len(next_examples) < 2:
                    next_examples.append(str(following["text"]))
                if following["terminal"]:
                    break

            if not crossed:
                continue
            aggregate["spill_events"] += 1
            aggregate["crossed_lines"] += crossed
            aggregate["extra_words"] += extra_words
            domain_counts[domain]["spill_events"] += 1
            domain_counts[domain]["crossed_lines"] += crossed
            domain_counts[domain]["extra_words"] += extra_words
            events.append(
                {
                    "domain": domain,
                    "nct_id": study["nct_id"],
                    "section": line["section"],
                    "cue_line": line["text"],
                    "next_lines": " || ".join(next_examples),
                    "crossed_lines": crossed,
                    "extra_words": extra_words,
                    "cue_line_is_bullet": line["bullet"],
                }
            )

    def derived(counts: Counter) -> dict[str, float | int]:
        neg = counts["negated_lines"]
        lines = counts["criteria_lines"]
        events_n = counts["spill_events"]
        return {
            **dict(counts),
            "bullet_line_pct": round(100 * counts["bullet_lines"] / lines, 1) if lines else 0,
            "negated_line_pct": round(100 * neg / lines, 1) if lines else 0,
            "spill_event_pct_of_negated": round(100 * events_n / neg, 1) if neg else 0,
            "mean_crossed_lines": round(counts["crossed_lines"] / events_n, 2) if events_n else 0,
            "mean_extra_words": round(counts["extra_words"] / events_n, 2) if events_n else 0,
        }

    summary = {
        "definition": (
            "A spill event is a negation-cue line without terminal punctuation followed by "
            "another line in the same eligibility section. A punctuation-only representation "
            "would keep the negation span open across that line break."
        ),
        "overall": derived(aggregate),
        "domains": {domain: derived(counts) for domain, counts in sorted(domain_counts.items())},
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    with (RESULTS / "spill_events.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(events[0]))
        writer.writeheader()
        writer.writerows(events)

    domain_rows = []
    for domain, counts in sorted(domain_counts.items()):
        domain_rows.append({"domain": domain, **derived(counts)})
    with (RESULTS / "domain_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = list(domain_rows[0])
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(domain_rows)

    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--limit", type=int, default=250)
    args = parser.parse_args()
    if args.fetch:
        fetch(args.limit)
    if not DATA.exists():
        raise SystemExit("No corpus found. Run with --fetch first.")
    analyze()


if __name__ == "__main__":
    main()
