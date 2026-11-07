# Git-register subject omission

## Paper

**Fix or *fixed*? Repository norms and subject omission in Git commits**

Authors: Sparsh and Kevin Zhou. The PDF remains anonymous for review.

Fourteen public repositories show a near-categorical community split between base-form and past-tense commit subjects. The paper argues that base morphology alone does not diagnose imperative force.

## Layout

- `paper/main.tex` - anonymous abstract source
- `output/pdf/plc51_abstract_anonymous.pdf` - final anonymous submission PDF
- `analysis/analysis.py` - corpus coding and statistics
- `analysis/manual_validation.py` - fixed-seed validation sample
- `analysis/fetch_data.sh` - pinned repository-history fetcher
- `results/` - coded observations and aggregate results

## Reproduce

```sh
./analysis/fetch_data.sh
python3 analysis/analysis.py
python3 analysis/manual_validation.py
```

## Build

```sh
mkdir -p output/pdf
pdflatex -interaction=nonstopmode -halt-on-error \
  -jobname=plc51_abstract_anonymous -output-directory=output/pdf paper/main.tex
```
