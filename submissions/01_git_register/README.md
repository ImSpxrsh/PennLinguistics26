# Git-register subject omission

## Paper

**One genre, two grammars: Community-conditioned subject omission in Git commit messages**

Fourteen public repositories show a near-categorical community split between base-form and past-tense commit subjects. The paper argues that base morphology alone does not diagnose imperative force.

## Layout

- `paper/main.tex` - anonymous abstract source
- `paper/abstract.pdf` - submission PDF
- `analysis/analysis.py` - corpus coding and statistics
- `analysis/fetch_data.sh` - pinned repository-history fetcher
- `results/` - coded observations and aggregate results

## Reproduce

```sh
./analysis/fetch_data.sh
python3 analysis/analysis.py
```

## Build

```sh
pdflatex -interaction=nonstopmode -halt-on-error \
  -jobname=abstract -output-directory=paper paper/main.tex
```
