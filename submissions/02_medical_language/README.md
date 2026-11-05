# Medical-language negation scope

## Paper

**Newlines are scope: Negation lost in clinical-trial text normalization**

The study analyzes 17,673 eligibility criteria from 970 structured ClinicalTrials.gov records. Newline flattening creates a possible cross-criterion negation spill in 42.8% of cue-bearing units; 90% of a deterministic 40-case audit separate independent sibling constraints.

## Layout

- `paper/main.tex` - anonymous abstract source
- `paper/abstract.pdf` - submission PDF
- `analysis/analysis.py` - API fetch and corpus analysis
- `data/studies.jsonl` - fixed public API snapshot
- `results/` - summaries, flagged events, and manual audit
- `notes/research_notes.md` - design decisions, limitations, and sources

## Reproduce

```sh
python3 analysis/analysis.py
```

To refresh the public snapshot:

```sh
python3 analysis/analysis.py --fetch --limit 250
```

## Build

```sh
pdflatex -interaction=nonstopmode -halt-on-error \
  -jobname=abstract -output-directory=paper paper/main.tex
```
