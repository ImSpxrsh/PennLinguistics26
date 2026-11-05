# Mechanistic interpretability of agreement

## Paper

**Encoded does not mean used: Causal separation of subject and attractor number in a Transformer**

DistilGPT-2 encodes both hierarchical subject number and nearest-noun number. Removing the late subject-number direction reduces agreement accuracy from 92.5% to 76.25%, while removing the more-decodable attractor direction leaves accuracy unchanged.

## Layout

- `paper/main.tex` - anonymous abstract source
- `paper/abstract.pdf` - submission PDF
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
pdflatex -interaction=nonstopmode -halt-on-error \
  -jobname=abstract -output-directory=paper paper/main.tex
```
