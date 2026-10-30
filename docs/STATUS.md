# Status — 2026-10-30

The public repository is https://github.com/hax2/wcsmatrix.

## Wiki frontier collection completed 2026-10-30

Pulled commit `18cceaf`, including the frozen **50-question HC3 Wiki CS/AI** domain and its complete local-only six-scorer matrix. Added **500 complete frontier answers**: 150 from the three closed models and 350 from the seven open-weight models. No filtered/truncated responses and no question exclusions.

API-reported cost: **$2.500031**. All request/text/prompt/provenance hashes passed, and the 300 existing Wiki local generations are reusable. The baseline Wiki config, prompts, human/local texts, and existing reports are unchanged.

Server command: `bash scripts/run_server.sh configs/wiki-comparison-frontier.yaml` after pulling. This targets **50 prompts × 17 sources × 6 scorers**. The new frontier WCS scores are not yet computed; current new reports contain collection statistics and integrity checks. See [the Wiki protocol](wiki-frontier.md).

Validation: lint and 20 tests passed, including the optional torch tests. Generation settings match the original ELI5 cohorts; keys and raw reasoning responses remain outside Git.

## Open-weight extension collected 2026-10-30

Added **350 hosted answers from seven open-weight models** on the same 50 frozen questions. **349 completed normally**; MiMo returned one `content_filter` response. Total API-reported cost: **$0.645730**. The filtered response is retained, marked incomplete, and excluded from WCS.

| Source | Complete / collected | Mean words (all collected) | Reported cost (USD) |
| --- | ---: | ---: | ---: |
| deepseek-v4-pro-0813 | 50 / 50 | 246.72 | 0.047402 |
| deepseek-v4.1-flash-1017 | 50 / 50 | 249.98 | 0.016664 |
| glm-5.3 | 50 / 50 | 366.16 | 0.065570 |
| kimi-k3 | 50 / 50 | 351.44 | 0.247392 |
| mimo-v2.6-pro | 49 / 50 | 301.36 | 0.020355 |
| minimax-m3 | 50 / 50 | 296.64 | 0.070938 |
| qwen3.8-2.4t-a95b | 50 / 50 | 325.20 | 0.177410 |

Use `configs/comparison-open-frontier-complete-cases.yaml` for a **49-prompt, 18-source × 7-scorer paired comparison**. It explicitly excludes `hc3-eli5-16977` from every source; this is a post-collection complete-case sensitivity analysis, not the original 50-prompt reproduction. `configs/comparison-open-frontier.yaml` preserves the full 50-prompt target and will flag the missing MiMo cell unless partial analysis is requested.

Weight references, commits, and licenses are in [the model manifest](open-frontier-models-20261030.json); the protocol and server commands are in [open-frontier.md](open-frontier.md). Actual giant weights were not downloaded: these are hosted source rows scored by the existing H100-feasible checkpoints. No new GPU WCS scores are claimed.

Validation: all 350 prompt/text/request/provenance identities passed; zero-new-request collection resumption passed. Lint and **20 tests** passed, including the optional torch architecture tests. The original baseline config, prompts, human answers, and 150 closed-frontier answers are unchanged.

## Original collection

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
