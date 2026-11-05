# Cherokee translation and romanization controls

## Paper

**Romanization or resolution? A shuffled-label control for Cherokee-English translation memory**

Unicode-label romanization improves in-domain translation-memory retrieval by 1.02 chrF2, but length-matched shuffled labels reproduce about 80% of the gain. The result shows that raw-versus-romanized comparisons can confound linguistic structure with increased character resolution.

## Layout

- `paper/main.tex` - anonymous abstract source
- `paper/abstract.pdf` - submission PDF
- `analysis/analysis.py` - retrieval, bootstrap, and shuffled controls
- `analysis/requirements.txt` - Python dependencies
- `results/` - aggregate and item-level outputs
- `notes/research_notes.md` - design decisions, limitations, and sources
- `data/` - local ChrEn download, excluded from Git

## Reproduce

Place the public ChrEn parquet splits in `data/chr_en/parallel/`, then run:

```sh
python3 -m pip install -r analysis/requirements.txt
python3 analysis/analysis.py
```

## Build

```sh
pdflatex -interaction=nonstopmode -halt-on-error \
  -jobname=abstract -output-directory=paper paper/main.tex
```
