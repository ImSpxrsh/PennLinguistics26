# Research notes: Cherokee transliteration audit

## Gap

Transliteration is frequently reported to help low-resource multilingual modeling and translation, especially when scripts diverge. A raw-script versus romanized comparison, however, changes more than linguistic representation: one syllabary symbol becomes several Latin characters, changing the resolution and overlap geometry of character n-gram models. Published comparisons rarely include a length- and inventory-matched nonlinguistic recoding control.

This candidate asks whether an apparent Cherokee romanization gain is genuinely attributable to the mapping between syllabary symbols and Latin syllable labels, or mostly to deterministic symbol expansion.

## Data and method

- Public ChrEn Cherokee-English corpus: 11,639 train, 1,000 development, 1,000 in-domain test, and 256 out-of-domain test pairs.
- Transparent translation-memory baseline: character n-gram TF-IDF on Cherokee, one-nearest-neighbor retrieval, and the retrieved pair's English side as the translation.
- Native-script and romanized n-gram ranges were independently selected on the development set from `(1,4)`, `(1,6)`, `(2,5)`, `(2,6)`, and `(2,8)`.
- Romanization is a deterministic, lossless mapping from each of 85 Cherokee symbols to the lowercased label in its Unicode character name.
- Twenty controls randomly permute romanized labels among Cherokee symbols **within label-length groups**. This preserves the label inventory and every symbol's expansion length while destroying the intended syllable-label association.
- Evaluation uses corpus chrF2 over English output; uncertainty is a 2,000-sample paired bootstrap over test items.

## Actual pilot results

- Development-selected ranges: 1-4 characters for both conditions.
- Native syllabary: 34.74 chrF2 in-domain; 18.54 out of domain.
- Romanized: 35.76 in-domain; 19.21 out of domain.
- Apparent in-domain gain: +1.02 chrF2, paired-bootstrap 95% interval `[0.49, 1.51]`; none of 2,000 bootstrap differences was non-positive.
- Length-matched shuffled controls: mean 35.55, SD 0.145, range 35.39-35.92.
- Two of 20 shuffled controls exceeded the linguistically labeled romanization. The romanized score is only +0.21 above the control mean; the controls account for about 80% of the raw-to-romanized gain.
- The in-domain to out-of-domain drop remains about 16 points for both systems. Romanization therefore does not solve domain shift.

## Interpretation

The raw-versus-romanized contrast is real but not causally diagnostic of phonological information. Most of the gain is reproduced when Latin labels are assigned to the wrong Cherokee symbols, provided the same expansion lengths and character inventory are preserved. Symbol expansion creates extra partial-overlap opportunities for character n-grams. Future transliteration claims should include matched recoding controls before attributing gains to phonological or cross-script alignment.

The Unicode-name mapping is an engineering diagnostic, not a proposed community orthography or pronunciation standard. Any community-facing Cherokee language technology should use speaker-approved representations and evaluation, following the collaboration principles in Zhang, Frey, and Bansal (2022).

## Primary sources

- Zhang, Frey, and Bansal (2020), ChrEn corpus and baselines: https://aclanthology.org/2020.emnlp-main.43/
- Zhang, Frey, and Bansal (2022), community-centered Cherokee NLP roadmap: https://aclanthology.org/2022.acl-long.108/
- Goyal, Kumar, and Sharma (2020), unified transliteration and subword segmentation for low-resource NMT: https://aclanthology.org/2020.acl-srw.22/
- Moosa, Akhter, and Habib (2023), transliteration effects in multilingual language modeling: https://aclanthology.org/2023.findings-eacl.50/
- Popovic (2015), chrF: https://aclanthology.org/W15-3049/

## Reproduction

Run `python3 analysis/analysis.py` after placing the public ChrEn parquet files under `data/chr_en/parallel/`. Exact aggregate results are in `results/results.json`; item-level test outputs are in `results/test_predictions.csv`.
