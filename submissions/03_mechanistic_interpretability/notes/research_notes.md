# Research notes: causal subject-number use in DistilGPT-2

## Gap

Agreement work increasingly identifies subject-number directions or specialized heads, but two issues remain easy to conflate:

1. a feature can be linearly decodable without being used for the model's prediction; and
2. attention specialization need not imply causal control of the output.

Number agreement with an attractor noun makes the distinction concrete. The structural subject and the nearest noun carry competing number values on incongruent items, so the experiment can compare what is encoded with what is causally used.

## Pilot completed on November 5, 2026

- Model: `distilgpt2` (81,912,576 parameters).
- Stimuli: 80 balanced prefixes: 10 held-out lexical groups x 2 subject numbers x 2 attractor numbers x PP/relative-clause structures.
- Behavioral measure: next-token logit contrast between single-token ` is` and ` are`.
- Diagnostic measure: group-five-fold logistic probes on the final prefix position at the embedding state and after all six transformer blocks. Lexical groups, not individual sentences, define folds.
- Causal measure: separately remove the centered one-dimensional subject- and attractor-number probe directions from the final-token residual stream, rerun the model, and compare the correct-inflection logit margin. Ten isotropic random directions serve as dimensionality-matched controls.

## Actual results

- Overall agreement accuracy: 92.5% (74/80).
- Congruent vs. incongruent: 97.5% vs. 87.5%.
- PP vs. relative clause: 100% vs. 85%.
- Best subject-number probe: 93.75% (state 5).
- Best attractor-number probe: 100% (states 3 and 4).
- Final-state subject-direction erasure reduced mean correct logit margin by 1.739; 10,000 paired bootstrap 95% CI [1.454, 2.017].
- Accuracy after final-state erasure: 76.25%; incongruent accuracy: 62.5%.
- Final-state attractor erasure changed the mean margin by only 0.005 and left overall/incongruent accuracy unchanged at 92.5%/87.5%.
- Mean final-state random-direction control accuracy: 92.5%; mean margin change: 0.002.
- The causal effect emerges late: mean margin drops are 0.030, 0.382, 0.817, and 1.739 after states 3-6.

Interpretation: nearest-noun number is at least as decodable as subject number, but removing the subject-number direction selectively damages agreement. Decodability therefore overstates the functional relevance of the attractor representation.

## Limits to state explicitly

- This is one small English autoregressive model and 80 controlled items.
- The intervention removes one linear direction, not a complete circuit.
- The causal direction is estimated on the full balanced stimulus set; follow-up work should cross-fit the intervention and replicate across seeds and model families.
- Relative-clause templates are deliberately controlled and sometimes semantically unusual.

## Primary sources

- Elazar, Ravfogel, Jacovi & Goldberg (2021), amnesic probing and the distinction between encoding and use: https://aclanthology.org/2021.tacl-1.10/
- Finlayson et al. (2021), causal mediation analysis of agreement mechanisms: https://aclanthology.org/2021.acl-long.144/
- Ryu & Lewis (2021), GPT-2 agreement attraction and attention: https://aclanthology.org/2021.cmcl-1.6/
- Eisape et al. (2022), causal intervention on incremental parse states: https://aclanthology.org/2022.findings-emnlp.203/
- Ferrando & Costa-jussa (2024), a causal subject-number direction in agreement circuits: https://aclanthology.org/2024.findings-emnlp.591/
- Dobrzeniecka, Fokkens & Sommerauer (2025), targeted alternatives for causal representation erasure: https://aclanthology.org/2025.findings-acl.674/
- Timkey & Linzen (2026), mixed causal evidence for specialized syntax heads: https://arxiv.org/abs/2610.19231
