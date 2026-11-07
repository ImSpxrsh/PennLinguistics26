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
- Causal measure: within each lexical fold, fit subject- and attractor-number directions and the center on eight lexical groups; apply each intervention only to the two held-out groups. Remove the one-dimensional direction from the final-token residual stream, rerun the model, and compare the correct-inflection logit margin. Ten fold-specific isotropic random directions serve as dimensionality-matched controls.

## Actual results

- Overall agreement accuracy: 92.5% (74/80).
- Congruent vs. incongruent: 97.5% vs. 87.5%.
- PP vs. relative clause: 100% vs. 85%.
- Best subject-number probe: 93.75% (state 5).
- Best attractor-number probe: 100% (states 3 and 4).
- Final-state subject-direction erasure reduced mean correct logit margin by 1.578; a 10,000-sample lexical-cluster bootstrap gives 95% CI [1.461, 1.688].
- Accuracy after final-state erasure: 66.25%; incongruent accuracy: 55%.
- The subject-minus-attractor erasure contrast is 1.578 logits, lexical-cluster bootstrap 95% CI [1.460, 1.686].
- Final-state attractor erasure changed the mean margin by less than 0.001 and left overall/incongruent accuracy unchanged at 92.5%/87.5%.
- Mean final-state random-direction control accuracy: 92.5%; mean margin change: 0.003.
- The causal effect emerges late: mean margin drops are 0.019, 0.332, 0.712, and 1.578 after states 3-6.
- The erasure effect is similar across PP and relative-clause items (1.616 versus 1.540 logits), but asymmetric by subject number. Singular accuracy falls to 42.5%; plural accuracy remains at 90%.

Interpretation: nearest-noun number is at least as decodable as subject number, yet the cross-fitted directions differ sharply in their causal effects. The result supports a contribution from a subject-correlated direction. It does not establish that every attractor representation is causally inert.

## Limits to state explicitly

- This is one small English autoregressive model and 80 controlled items.
- The intervention removes one linear direction, not a complete circuit.
- Each causal direction and center is fit without the held-out lexical groups. Replication across model families and larger stimulus sets is still needed.
- The final erasure effect is concentrated on singular-subject items, so the fitted direction may combine number with a singular-specific output bias.
- Relative-clause templates are deliberately controlled and sometimes semantically unusual.

## Primary sources

- Elazar, Ravfogel, Jacovi & Goldberg (2021), amnesic probing and the distinction between encoding and use: https://aclanthology.org/2021.tacl-1.10/
- Finlayson et al. (2021), causal mediation analysis of agreement mechanisms: https://aclanthology.org/2021.acl-long.144/
- Ryu & Lewis (2021), GPT-2 agreement attraction and attention: https://aclanthology.org/2021.cmcl-1.6/
- Eisape et al. (2022), causal intervention on incremental parse states: https://aclanthology.org/2022.findings-emnlp.203/
- Ferrando & Costa-jussa (2024), a causal subject-number direction in agreement circuits: https://aclanthology.org/2024.findings-emnlp.591/
- Dobrzeniecka, Fokkens & Sommerauer (2025), targeted alternatives for causal representation erasure: https://aclanthology.org/2025.findings-acl.674/
- Timkey & Linzen (2026), mixed causal evidence for specialized syntax heads: https://arxiv.org/abs/2610.19231
