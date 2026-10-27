# Expansion plan

## Frontier sources (implemented first)

Question: under the same seven open scorers, how much of frontier-generated text remains inside the scorer's nucleus compared with human answers and greedy open-model answers?

Use the same frozen 50 question IDs for GPT-6 Astra, Claude Opus 5.5, and Gemini 4 Argon. Preserve them as explicit frontier rows with source metadata. Their role in the matrix is the same as the human reference row; their provenance is never changed to human. `human-minus-source.csv` reports each of these contrasts per scorer.

A lower frontier WCS would show less lexical coverage by these scorers, not proof of human-like thought, originality, superior quality, or detection resistance. No closed-model scorer direction is inferable from these rows alone.

## Sensitivity studies before scaling

Copy the YAML into a named config and use a new `name`, generation output path when relevant, and source identifiers when mixing conditions.

1. Hold texts fixed and compare `word_policy: whitespace` versus `lexical`; this changes only `rescore`/analysis. Check separately whether HC3's spaced punctuation changes the human gap.
2. Hold texts fixed and compare `context_mode: chat`, `plain`, and `text_only`; these require new audits. This tests dependence on the question and chat framing.
3. Compare p=.90/.95/.99 and realistic/strict/strict_full using existing token audits. Monitor how often an observed token falls outside top-100 and where the strict truncation diagnostic diverges.
4. Generate register-matched forum answers and sampled local answers (`do_sample: true`, explicit temperature/top_p). Use distinct source names/output files and preserve the greedy baseline. Distinct configurations are separate experiments; automatic cross-condition pooling is intentionally not implemented.
5. Compare bf16 and int8 for a small checkpoint on the same texts before interpreting quantized-model differences. Set the new model name and experiment name to avoid collisions.

## E1–E4 from the draft (not yet run)

- E1: 250 prompts per dataset across HC3, M4, RAID, MAGE; eight models and three families.
- E2: 22×22 size/stage/version matrix with 500 prompts.
- E3: nine-model directional matrix including Olmo, plus open-ended Infinity-Chat prompts.
- E4: sampled decoding, forum-register prompts, and post-cutoff human writing.

Only the HC3 adapter is implemented. Additional datasets need adapters producing the same frozen prompt/human schema, licensed source attribution, genuinely comparable prompts, domain labels, and a prespecified sampling plan. Adding a dataset name to YAML alone does not implement an experiment. The current analysis groups one configured dataset; stratified per-domain and pooled multi-dataset analysis must be added before E1 claims.

Prioritize a fully reproduced 50-question result, numerical/word-policy controls, and a few independently sampled runs before the larger plan. The 38 GiB budget rules out bf16 large checkpoints and may require smaller model subsets or explicit int8 variants. Never silently replace a requested model with a different size or lower precision.
