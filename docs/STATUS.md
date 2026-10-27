# Status — 2026-10-27

The private repository is https://github.com/hax2/wcsmatrix.

## Collected

50 frozen HC3 ELI5 questions and selected human answers, plus 150 complete frontier-generated answers:

| Source | Complete answers | Mean words | API-reported cost (USD) |
| --- | ---: | ---: | ---: |
| GPT-6 Astra | 50 | 262.54 | 0.918220 |
| Claude Opus 5.5 | 50 | 364.96 | 0.776524 |
| Gemini 4 Argon | 50 | 352.38 | 0.235778 |
| Human HC3 reference | 50 | 234.56 | — |

Total reported generation cost: **$1.930522**. All API finish reasons were `stop`. One Claude answer has 404 whitespace-delimited words and is retained with the length deviation reported. No human reference answer was sent to an API.

The collected texts and provenance are versioned. Existing local API credentials were loaded in place; their values and source credential files are excluded from the repository. A zero-new-request resumption run verified that complete matching outputs are reused.

## Validated locally

- Lint passed.
- 12 CPU/data/API/analysis tests passed in the lightweight locked environment; torch-dependent tests are skipped there.
- All **16 tests passed** with installed PyTorch 2.13.0 and the locked Transformers 5.21.0 in a separate environment.
- Chunked teacher forcing agrees with unchunked scoring for tiny random Qwen3.5, Gemma4, and Gemma4Unified language models under SDPA, and with an explicit full-context oracle.
- Actual pinned Qwen and Gemma tokenizers passed prompt/answer boundary and offset checks.
- Pinned model configurations resolve to supported multimodal model classes under Transformers 5.21.0. An older locally installed Transformers 5.5.4 lacked Gemma4Unified support; use the lockfile.

## Still requires the H100 server

The seven full checkpoints have not been generated/scored here. Their half-memory H100 loading, int8 behavior, throughput, and numerical results remain unvalidated. The GPU dependency lock selects PyTorch 2.14.1, so that exact GPU stack still requires the server smoke test. Start with the two-question one-model smoke config, then run the full script described in the README.

No WCS values for the new collection, replication agreement, human/frontier gap, or family effects are claimed yet. The current report directory contains collection statistics only. Full analysis becomes available after GPU generation and audits.
