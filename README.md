# Penn Linguistics Conference 51

Anonymous abstract and reproducibility materials for a study of subject omission in Git commit messages.

## Files

- `abstract/plc51_abstract_anonymous.pdf` - submission-ready two-page PDF
- `abstract/main.tex` - editable LaTeX source
- `analysis/analysis.py` - corpus coding and statistical summary
- `analysis/fetch_data.sh` - fetches the pinned public repository histories
- `results/coded_commits.csv` - coded observations used in the abstract
- `results/summary.txt` - aggregate counts

## Reproduce the analysis

```sh
./analysis/fetch_data.sh
python3 analysis/analysis.py
```

## Build the abstract

```sh
pdflatex -interaction=nonstopmode -halt-on-error \
  -output-directory=abstract abstract/main.tex
```

The submitted PDF is anonymous and contains no author or affiliation metadata.
