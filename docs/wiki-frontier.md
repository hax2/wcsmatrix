# Wiki CS/AI frontier extension

The dataset pulled in commit `18cceaf` is HC3's **Wiki CS/AI** subset (`wiki_csai`), not a new independently collected corpus. It contains 50 frozen questions, selected human answers, 300 greedy answers from six local models, and the server's corresponding local-only WCS matrix. Its prompts, human texts, local texts, and original `configs/wiki.yaml` are preserved.

This extension generates answers from the **same three closed-frontier and seven open-weight-frontier model IDs** used on ELI5, on those exact 50 Wiki prompts. It keeps the original per-cohort generation settings so a dataset comparison does not also intentionally change sampling/reasoning:

| Cohort | Sources | Requested generation settings |
| --- | --- | --- |
| Closed frontier | GPT-6 Astra, Claude Opus 5.5, Gemini 4 Argon | Low reasoning, reasoning excluded from returned content, 4096-token cap; sampler fields omitted as in the ELI5 closed cohort |
| Open-weight frontier | Qwen3.8-2.4T-A95B, DeepSeek V4 Pro 0813, DeepSeek V4.1 Flash 1017, GLM-5.3, Kimi K3, MiniMax M3, MiMo V2.6 Pro | Temperature 1.0, top-p .95, top-k 0, seed 42, 8192-token cap; low reasoning where supported, otherwise reasoning enabled; reasoning excluded from returned content |

The same neutral 150–400-word instruction from `data/prompts/wiki-50.jsonl` is used throughout. Human answers are not sent to generation APIs. Reference weight metadata for open models is preserved, while exact provider weight revisions/precision remain unverified. API aliases and provider implementations can evolve between the ELI5 and Wiki collection dates, and the open/closed cohorts have different sampler/reasoning conditions. Neither comparison isolates a model-quality or open/closed-weights causal effect.

## Files

- `configs/wiki-closed-frontier.yaml` → `data/texts/wiki-closed-frontier-20261030.jsonl`
- `configs/wiki-open-frontier.yaml` → `data/texts/wiki-open-frontier-20261030.jsonl`
- `configs/wiki-comparison-frontier.yaml` → combined analysis, using both files plus the original human and local texts
- `docs/wiki-{closed,open}-frontier-catalog-20261030.json` → catalog snapshots used for availability/parameter/price checks
- `results/reports/hc3-wiki-50-comparison-frontier-20261030/` → collection statistics and validation; WCS artifacts are added after GPU scoring

All source answers have text/prompt/request hashes, requested/returned model IDs, provider, timestamp, finish reason, and usage/cost metadata. Incomplete or filtered responses remain recorded and are excluded from WCS. Any complete-case subset is declared explicitly in a separate config rather than silently dropping questions.

## Run on the server

After the frontier collection has been pushed:

```bash
git pull --ff-only
uv sync --python 3.12 --extra gpu --extra dev
bash scripts/run_server.sh configs/wiki-comparison-frontier.yaml
```

This targets **17 source rows × 6 scorer columns**: human, six greedy local sources, three closed-frontier sources, and seven open-frontier sources. The six scorers are the original Wiki suite (Qwen 2B/4B/9B and Gemma E2B/E4B/12B); no large hosted frontier model is loaded as a scorer on the half-memory H100. Local generation is reused when its request identities match. The new experiment name keeps the local-only Wiki report intact; the new audit directory is separate.

The pulled server runner explicitly requests partial analysis. Inspect `completeness.json` and `analysis-manifest.json` before using a matrix; `partial: false` is required for the full configured comparison. To demand strict analysis after scoring:

```bash
uv run wcsmatrix --config configs/wiki-comparison-frontier.yaml analyze
```

`matrix.csv` and heatmaps compare individual sources. `human-minus-source.csv` contains paired prompt-bootstrap intervals for each human/model contrast. `source-group-contrasts.csv` reports open-minus-closed, open-minus-greedy-local, and closed-minus-greedy-local mean coverage, with sources averaged within each prompt before prompt-paired bootstrapping. Intervals use 10,000 replicates and seed 42. Source-row averages give the open cohort's two DeepSeek checkpoints two votes; these are not family-balanced averages.

The draft paper's reported numeric targets concern ELI5; a Wiki `paper-comparison.csv`, if produced by the current generic reporting code, is a cross-domain descriptive difference and **not** a replication agreement result. Compare Wiki with the stored ELI5 matrices using dataset labels and matched source/scorer settings.

## Resume API collection locally

Use the separate collection configs, not the analysis-only combined config:

```bash
uv run wcsmatrix --config configs/wiki-closed-frontier.yaml frontier \
  --env-file /absolute/path/to/credentials.env --workers 6 --max-cost-usd 20
uv run wcsmatrix --config configs/wiki-open-frontier.yaml frontier \
  --env-file /absolute/path/to/credentials.env --workers 7 --max-cost-usd 20
```

Matching saved outputs are reused, including recorded incomplete responses; resumption does not reroll a provider refusal. The cost flag checks a token-price estimate and is not a provider billing cap. No API key is needed on the server to score the already collected source texts.

## Collection completed

All **500 frontier answers completed normally**, with 50 answers per model and no prompt exclusions. API-reported cost: **$2.500031** (closed: $1.960038; open: $0.539993). All prompt/text/request/provenance hashes passed validation. The existing 300 local-answer request identities match the combined config, so server generation can reuse them. Actual frontier WCS scoring remains pending on the H100.
