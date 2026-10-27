# Reproduction contract and known gaps

Source: `wcs_paper_acl_v3_94GB.pdf`, “Who Covers Whom? Word Coverage Matrices for Human Text and for LLMs of the Same and Different Families,” anonymous ACL submission, supplied by the user. This is a draft: Section 4 reports one measured run; E1–E4 in Section 5 are proposed experiments and contain [XX] placeholders. We do not treat those as measured results.

## Fixed choices

- HC3 `reddit_eli5.jsonl`, frozen dataset commit, 50 questions, seed 42.
- Raw HC3 subset has no `id` field: we use its zero-based source line index, prefixed `hc3-eli5-`. Choose the first human answer of 150–400 whitespace-delimited words per question, sort candidate IDs lexicographically, then Python `random.Random(42).sample`. The output manifest is authoritative and versioned.
- One neutral English answer prompt, requesting 150–400 words. Human answers are never sent to the generation API. The same question/instruction is used for all local/API sources. We retain natural length variation and report out-of-range answers rather than trimming them or selecting better-looking generations.
- Greedy open-model generation with a 1024-token cap; source and scorer are identical pinned checkpoints. Qwen thinking is disabled in its chat template; no manual removal of text after generation. Frontier models use their documented low-reasoning settings and are labeled separately; no greedy-equivalence claim.
- Teacher forcing uses each scorer's own chat template and the question prompt, then appends the observed answer. Human/API/open-model answers use the same scorer-specific prefix. `context_mode: plain` and `text_only` are configurable sensitivity controls.
- Score only visible answer tokens, including the first answer token. Exclude chat prefix and EOS from WCS. Refuse prompt/answer boundary token merges and context overflow rather than silently corrupting alignment or truncating.
- Temperature 1 for the scoring distribution. Compute full-vocabulary softmax in float32 from model logits. Default chunk size is 128 input tokens, with the full preceding context carried through KV cache; no context-window resets between words or chunks.
- Default word unit: a non-whitespace span, punctuation included, covered iff **every** overlapping tokenizer token survives. HC3's punctuation is often separately space-delimited, so this choice matters. `word_policy: lexical` is an alternative Unicode word convention using `\b\w+(?:['’-]\w+)*\b`. A token overlapping two words contributes to both. Neither policy is claimed to match an unspecified original convention.

## Three nucleus metrics

1. **realistic** (paper's primary): keep sorted top-100 probabilities, normalize by their sum, find the top-p nucleus, then test the observed token. An observed token absent from the stored top-100 is excluded.
2. **strict** (paper-style stored distribution): use unnormalized full-softmax top-100 probabilities for the nucleus. An observed token absent from the stored top-100 is excluded, even if the stored mass does not reach p. This is a truncated-support measurement.
3. **strict_full** (extension diagnostic): use the full-vocabulary probability mass ranked above the observed token, stored at inference time. This resolves the tail ambiguity that cannot be settled from top-100 alone. Ties use mass of strictly higher-probability tokens, which can include an entire boundary tie group; stored top-k membership uses the inference engine's tie order.

Retain the token that crosses p. To follow the locally available upstream WCS convention, a token survives when cumulative probability *before* it is `<= p`. The exact equality boundary may differ from some generation libraries but is rare with ordinary logits. We deliberately retain strict_full as a separate metric, never relabeling it as the paper's strict result.

The identity of the observed token, top-100 token IDs/probabilities, relative character offsets, prefix string, and mass-before statistic are saved, so word policies and p values can be recomputed offline. Scorer revision/precision, context settings, text, and prompt are hashed; changed inference identities require a new experiment name. Changed generation settings require a new text output path.

## What cannot be exactly reproduced yet

The paper does not provide its 50 curated question IDs, answer-selection decisions, exact prompt, checkpoint commits, tokenizer versions, word-boundary definition, prompting context for scoring, generation length cap, numerical precision settings beyond int8/bf16, or per-prompt raw results. The bibliography's earlier WCS paper does not replace those missing artifacts. Hence numeric discrepancies are evidence to investigate, not immediately a failed theoretical claim.

The local `/home/Shodan/WCS` project (`https://github.com/WordsGPT/WCS`) informed the all-subtoken survival rule and nucleus crossing convention. This repo is standalone and does not import that checkout or copy its credentials. The paper's 0.015–0.089 engine differences reinforce the need to record engine versions before interpreting a small change.

## Statistical reporting

For each scorer, compare human and each local/frontier source on exactly matched prompt IDs. Bootstrap the per-prompt differences, not words or separately sampled sources. Matrices use the mean of per-prompt WCS. Family contrasts average same-family or cross-family local-model cells per prompt, excluding self, then bootstrap prompts. Frontier rows are excluded from that particular local-family contrast. Pairwise direction contrasts compare `scorer A ← source B` with `scorer B ← source A` on shared prompts.

Default analysis demands complete configured matrices. `--allow-partial` marks output as partial and records each missing cell in `completeness.json`; each contrast reports n. Missing cells are never filled with zero. The pointwise intervals reproduce the paper's reporting convention, not a familywise significance guarantee.

Paper targets in `paper-targets.json` are rounded human-row values from Tables 1 and 4, not raw data. Compare with this rounding limitation in mind. The draft's “97 of 98” includes two metrics and seven scorer × seven LLM comparisons; do not apply that count to the enlarged matrix.

## Primary references checked during setup

- HC3 dataset and license: https://huggingface.co/datasets/Hello-SimpleAI/HC3
- Qwen checkpoint/use: https://huggingface.co/Qwen/Qwen3.5-9B
- Qwen Transformers architecture: https://huggingface.co/docs/transformers/main/en/model_doc/qwen3_5
- Gemma model card: https://huggingface.co/google/gemma-4-12B-it
- OpenRouter model catalog: https://openrouter.ai/api/v1/models
- OpenRouter request schema: https://openrouter.ai/docs/api_reference/overview
- OpenAI current models: https://developers.openai.com/api/docs/guides/latest-model
- Gemini current models: https://ai.google.dev/gemini-api/docs/models

Retrieved 2026-10-27. Checkpoint and dataset commits are pinned in YAML; API model aliases can evolve, so response identity and catalog metadata are retained.
