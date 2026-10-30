# Frontier open-weight source extension — 2026-10-30

This cohort adds hosted generations from seven large open-weight checkpoints on the **same 50 frozen HC3 ELI5 prompts** as the paper reproduction and the existing proprietary-frontier collection. We verify downloadable safetensors weights in each maker's repository, archive its commit and declared license, and preserve the hosted model/provider identity on every answer. This is a cross-family, high-capacity cohort, not a claim that these seven exhaust every current frontier release or have a universal benchmark ranking.

## Model selection and weights

| Source | Reference weights | Approximate total parameters | Declared license |
| --- | --- | ---: | --- |
| Qwen3.8-2.4T-A95B | [Qwen/Qwen3.8-2.4T-A95B](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B) | 2.45T | Qwen3.8-Max custom |
| DeepSeek-V4-Pro-0813 | [deepseek-ai/DeepSeek-V4-Pro-0813](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813) | 1.65T | MIT |
| DeepSeek-V4.1-Flash-1017 | [deepseek-ai/DeepSeek-V4.1-Flash-1017](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017) | 763B | MIT |
| GLM-5.3 | [zai-org/GLM-5.3](https://huggingface.co/zai-org/GLM-5.3) | 753B | GLM-5.3 custom |
| Kimi-K3 | [moonshotai/Kimi-K3](https://huggingface.co/moonshotai/Kimi-K3) | 2.78T | Kimi-K3 custom |
| MiniMax-M3 | [MiniMaxAI/MiniMax-M3](https://huggingface.co/MiniMaxAI/MiniMax-M3) | 427B | MiniMax Community |
| MiMo-V2.6-Pro | [XiaomiMiMo/MiMo-V2.6-Pro-RL](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Pro-RL) | 1.02T | MIT |

Totals come from the model repositories' safetensors metadata, not the number of active MoE parameters. `open-frontier-models-20261030.json` contains exact counts, reference commits, license names, and verified weight-file counts. Custom licenses are preserved as declared; downloadable weights do not imply an OSI-approved open-source license.

DeepSeek contributes both its high-capacity Pro checkpoint and the newer Flash checkpoint. Kimi K3 is used because its weights are published; a newer hosted Kimi alias without verified downloadable weights does not qualify for this cohort. MiniMax M3 is the high-capacity family anchor; the newer M3.1-Flash efficiency model is not included. The API catalog/Hugging Face mapping alone is not proof that a provider serves the exact reference commit or precision: `provider_weight_revision_verified` remains false. We do not claim bit-for-bit local/API equivalence.

## Generation condition

`configs/open-frontier.yaml` is the authoritative generation config. It writes to a **new** `data/texts/open-frontier-20261030.jsonl`; original frontier answers and the reproduction YAML are unchanged.

Every new request explicitly sends:

```json
{
  "temperature": 1.0,
  "top_p": 0.95,
  "top_k": 0,
  "seed": 42,
  "max_tokens": 8192,
  "provider": {"require_parameters": true}
}
```

Reasoning effort is `low` where supported (Qwen, DeepSeek, GLM, Kimi). MiniMax and MiMo use `reasoning.enabled: true` without an unsupported effort field. All requests set `reasoning.exclude: true`. This requests omission of reasoning from returned content, not disabling reasoning. Raw responses, if they contain reasoning, remain ignored and local.

`top_k: 0` requests no top-k cutoff; top-p=.95 remains active. Provider implementation and seed determinism are not independently verified; we record submitted settings rather than claiming control over undisclosed internals. Penalties, min-p, and other unlisted controls are not set. The larger 8192-token cap gives these reasoning models headroom; the original closed-frontier condition used 4096 and provider-default sampling. Open/closed contrasts therefore include decoding/reasoning differences, not solely weight access or model quality.

The generation prompt is unchanged: answer the question in English in 150–400 words and return only the answer. We retain and report length deviations; we never cut answers to make them fit. All settings and reference-weight metadata contribute to the request identity. Changing them requires new text paths. A truncated completion is kept in the collection, marked incomplete, and excluded from WCS; a full 50-question comparison then requires a separately identified replacement condition.

## Collect or resume locally

```bash
uv run wcsmatrix --config configs/open-frontier.yaml frontier \
  --env-file /absolute/path/to/credentials.env --workers 7 --max-cost-usd 20
uv run wcsmatrix --config configs/open-frontier.yaml analyze
```

The cost flag is the existing catalog-price planning check, not a provider-enforced billing cap. `docs/open-frontier-catalog-20261030.json` archives the catalog fields used to plan and validate this collection. The texts carry `kind: frontier` and `source_metadata.weights_access: open_weights`; they are never relabeled human or locally generated.

## Compare on the H100

These reference checkpoints do not fit the 38 GiB GPU allocation at bf16/int8. Even the smallest has more than 400B total parameters. Hosted generation adds **source rows**; our seven existing local checkpoints remain the **scorers**. No giant weight files are downloaded into this repo. To score the frontier checkpoints themselves would require substantially different hardware/inference and is not implemented here.

One MiMo response on `hc3-eli5-16977` was stopped by `content_filter`; the other 349 responses completed normally. The raw 50-question collection is preserved. A separate `configs/comparison-open-frontier-complete-cases.yaml` config explicitly excludes that one question from **every** source/scorer, giving 49 matched prompts. This is a post-collection complete-case sensitivity analysis and may introduce selection bias; the original reproduction remains on its 50 questions. The full 50-question comparison config remains available and requires `--allow-partial` to analyze the missing MiMo cell.

On the server, after pulling the collected texts:

```bash
git pull --ff-only
uv sync --python 3.12 --extra gpu --extra dev
# Run the README's real GPU smoke test first if it has not already passed.
bash scripts/run_server.sh configs/comparison-open-frontier-complete-cases.yaml
```

Both comparison configs read the original closed-frontier file plus `additional_texts` pointing to the new open-frontier file. Each uses a new experiment name, the frozen human prompts, the original seven model/scorer specs, and the original greedy local-generation settings. Existing local-generation rows are reused when their request identities match. Existing baseline audit files remain under the old experiment; the combined experiment gets its own audited matrix.

The result has **18 source rows × 7 scorer columns**: human, seven local sources, three proprietary-frontier sources, and seven open-frontier sources. Besides the matrix and human-minus-source intervals, `source-group-contrasts.csv` gives open-frontier minus proprietary-frontier and open-frontier minus greedy-local means. Each group first averages source scores within a prompt, then resamples paired prompts. The seven-model open cohort gives DeepSeek two rows; group averages weight source rows equally, not families equally. Individual source rows remain available for family-balanced follow-up analysis.

Both combined configs are deliberately disabled for API collection, so they cannot append newly configured models/settings into the original closed-frontier file. Generate with `open-frontier.yaml`; score/analyze the 49-prompt matched set with `comparison-open-frontier-complete-cases.yaml`. To retain all 50 prompts, run `generate` and `audit` with `comparison-open-frontier.yaml`, then explicitly run `analyze --allow-partial`; the all-in-one server script deliberately requires a complete matrix and will stop at strict analysis for that config. Strict analysis still refuses incomplete configured matrices, and no GPU WCS result is claimed until the server audits run.

Collection result: 350 responses, 349 normal completions, one retained content-filter response; API-reported cost **$0.645730**. The frozen data are in `data/texts/open-frontier-20261030.jsonl`; the collection statistics and integrity checks are under `results/reports/hc3-50-open-frontier-20261030/`. The zero-new-request resume check confirms these rows are reused without re-generation.
