# Mechanistic interpretability of agreement

## Paper

**Cross-fitted causal erasure separates subject and attractor number in DistilGPT-2**

Authors: Sparsh and Kevin Zhou. The submission PDF is anonymized for review.

DistilGPT-2 encodes both hierarchical subject number and nearest-noun number. Agreement accuracy is 92.5% before group-cross-fitted erasure of a subject-correlated direction and 66.25% afterward. Erasure of the fitted attractor direction leaves accuracy unchanged.

## Layout

- `paper/main.tex` - anonymous abstract source
- `output/pdf/plc51_abstract_anonymous.pdf` - final anonymous submission PDF
- `analysis/analysis.py` - stimuli, probes, and causal interventions
- `analysis/requirements.txt` - Python dependencies
- `results/` - item-, layer-, and summary-level outputs
- `notes/research_notes.md` - design decisions, limitations, and sources

## Reproduce

```sh
python3 -m pip install -r analysis/requirements.txt
python3 analysis/analysis.py
```

## Build

```sh
mkdir -p output/pdf
pdflatex -interaction=nonstopmode -halt-on-error \
  -jobname=plc51_abstract_anonymous -output-directory=output/pdf paper/main.tex
```
