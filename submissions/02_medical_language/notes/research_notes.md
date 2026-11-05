# Research notes: line breaks and clinical negation scope

## Question and gap

Clinical trial eligibility parsers treat negation as a core semantic attribute, but the literature mainly evaluates lexical cues, entity relations, and decomposed logical traits. A basic representational choice is underexamined: ClinicalTrials.gov criteria are commonly authored as Markdown-style lists, while downstream preprocessing often turns records into undifferentiated free text. The pilot asks how often a newline or list-item boundary is the only overt boundary preventing a negation cue from extending into the next criterion.

The claim is deliberately narrow. The analysis measures **scope-spill opportunities under punctuation-only normalization**, not end-to-end model errors. A gold-standard evaluation would require clinician annotation of original/flattened minimal pairs.

## Data

- Public ClinicalTrials.gov API v2 snapshot collected November 5, 2026.
- The 250 most recently updated recruiting trials returned for each of four condition queries: cancer, heart disease, diabetes, and depression.
- Records were deduplicated across queries, yielding 989 studies; 970 contained explicit bullet or numbered criteria.
- The analysis retained 17,673 structured criteria units.
- Raw API records are in `data/studies.jsonl`; code is in `analysis/analysis.py`.

## Operationalization

Negation cues: `no`, `not`, `without`, `never`, `neither`, `cannot`, `can't`, `must not`, `may not`, `absence of`, `free of`, and `negative for`.

A boundary-sensitive event occurs when:

1. a bullet/numbered criterion contains a cue;
2. that criterion lacks terminal punctuation (`. ! ? ; :`); and
3. another criterion follows in the same inclusion/exclusion section.

The punctuation-only baseline replaces the intervening newline with a space and holds scope open until terminal punctuation. Wrapped prose inside one bullet is joined before measurement, so ordinary display wrapping is not counted as a criterion boundary.

## Pilot results

- 2,084 of 17,673 criteria units (11.8%) contained a negation cue.
- 892 of those 2,084 units (42.8%) were boundary-sensitive.
- The punctuation-only baseline crossed a median of 4 following criteria and 67 words per event.
- Rates by domain: oncology 47.7%, diabetes 42.4%, cardiology 42.0%, psychiatry 32.5%.
- Domain differences: chi-square(3) = 28.05, p < .001, Cramer's V = .116.
- A deterministic random audit of 40 events (10 per domain; seed 51) found that 36/40 (90%) were independent sibling constraints. Four were coordinated or nested continuations. The audit is recorded in `results/manual_audit.csv` and motivates an exception for overt continuation markers and indentation.

An attested exclusion-list sequence from NCT07318805 is:

> Hypertension that cannot be controlled by optimal medical therapy  
> Renal impairment  
> Hepatic dysfunction

The latter two lines are sibling exclusions, not complements of `cannot`; deleting list boundaries produces a misleading contiguous negation span.

## Proposed contribution

Treat same-level list boundaries as hard scope boundaries and preserve them as typed sentinels before tokenization. Wrapped continuations remain within a unit; nested list items can be attached to a parent using indentation. The proposal is compatible with rule-based and neural negation systems and yields a natural robustness benchmark: original criteria versus newline-flattened minimal pairs.

## Limitations

- Cue matching is lexical and intentionally conservative, not a gold-standard negation annotation.
- The sample is a recent, stratified snapshot rather than a random sample of all registered trials.
- A boundary-sensitive event is a structural risk, not proof that a particular deployed parser makes an error.
- Some authoring inconsistencies remain even after wrapped lines are joined.
- The manual audit was performed by one reviewer on a small sample; a clinician-annotated scope benchmark remains necessary.

## Sources

- ClinicalTrials.gov API: https://clinicaltrials.gov/data-api/api
- Chapman et al. (2001), NegEx and clinical negation scope: https://doi.org/10.1006/jbin.2001.1029
- Yuan et al. (2019), Criteria2Query: https://doi.org/10.1093/jamia/ocy178
- Fang et al. (2022), Criteria2Query 2.0 and negation-scope evaluation: https://doi.org/10.1093/jamia/ocac051
- Dobbins et al. (2022), Leaf Clinical Trials Corpus: https://doi.org/10.1038/s41597-022-01521-0
- Kantor and Morzy (2024), scoping review and benchmark gap: https://doi.org/10.1016/j.drudis.2024.104139
- Chen et al. (2026), decomposition, nested logic, and explicit negation annotation: https://doi.org/10.3233/SHTI250928

