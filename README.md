# Who Covers Whom? — reproduction and frontier-source extension

Recreate the scorer-by-source Word Coverage Score (WCS) matrix in the supplied ACL draft and test whether frontier-generated answers sit closer to human or open-model text under the same open-model scorers.

**Baseline scope:** 50 fixed HC3 ELI5 questions; human text, seven open-model sources, and three frontier sources; seven open-model scorers. Frontier models contribute source rows, while human remains its own row. API access does not provide the teacher-forced distributions needed for frontier scorer columns.

The paper's exact curated question IDs, prompts, tokenizer conventions, and inference configuration are unavailable. This is a documented independent reproduction, with rounded targets transcribed from Tables 1 and 4. See [methodology](docs/methodology.md) for the choices that can affect agreement.

## Open-weight frontier extension

Seven additional large open-weight models are configured in [the open-frontier extension](docs/open-frontier.md). Their answers use the same frozen questions and explicit sampler settings. Use `configs/open-frontier.yaml` for collection and `configs/comparison-open-frontier-complete-cases.yaml` for the combined 18-source × 7-scorer matrix on 49 matched prompts. One MiMo content-filter response is retained in the full 50-question collection; `configs/comparison-open-frontier.yaml` preserves that full target for explicitly partial analysis. The original baseline config and frontier texts remain unchanged.

## Wiki CS/AI frontier extension

The newly pulled Wiki CS/AI dataset has its own [frontier extension](docs/wiki-frontier.md), using the same three closed and seven open frontier models on its frozen 50 questions. Use `configs/wiki-comparison-frontier.yaml` on the server to compare them against the six existing local models. The original Wiki and ELI5 experiments remain separate.

## Local setup and frontier collection

```bash
uv sync --extra dev
uv run pytest -q
uv run wcsmatrix prepare
# Reads keys in place; does not copy the credential file.
uv run wcsmatrix frontier --env-file /absolute/path/to/existing/.env.local --workers 6 --max-cost-usd 20
uv run wcsmatrix analyze
```

`frontier` resumes from existing answers, validates request hashes, checks current model availability, and records requested/returned model IDs, provider, request settings, finish reason, timing, usage, and reported cost. Its cost flag is a preflight bound from current catalog token prices for new requests, not a provider-side billing cap. API retry billing and pricing changes are outside that estimate. Successful outputs survive failed requests. The configured API output limit includes reasoning tokens. Truncated answers stay recorded but are excluded from WCS.

Versioned `data/texts/frontier.jsonl` contains visible answers and provenance, never keys or hidden reasoning. The full raw API responses and token audit arrays remain ignored. The corresponding model catalog snapshot is in `docs/frontier-catalog.json`. API generations are not guaranteed deterministic and are a separate decoding condition from the greedy open-model replication.

## H100 server (about 40 GiB available)

```bash
git clone https://github.com/hax2/wcsmatrix.git
cd wcsmatrix
# Or git pull --ff-only in an existing clone.
uv sync --python 3.12 --extra gpu --extra dev
uv run --extra gpu pytest -q

# First confirm model access and run two prompts through a small model.
uv run wcsmatrix --config configs/smoke.yaml prepare
bash scripts/run_server.sh configs/smoke.yaml

# Full 7-scorer × 11-source run, including already-collected API answers.
bash scripts/run_server.sh configs/reproduction.yaml
```

The GitHub repository is public and can be cloned without authentication. Accept model terms and set `HF_TOKEN` if your account is asked for access. No OpenRouter key is needed on the server when the collected answers are present. `uv.lock` pins resolved dependencies; `uv sync` selects the extras for that machine. Keep the lockfile unchanged for comparisons. CUDA drivers must support the installed PyTorch wheel.

Models load sequentially with bf16 weights, except Qwen3.5-27B in bitsandbytes int8. The default process budget is **38 GiB**, with 4 GiB reserved beyond estimated weight placement. The loader checks free VRAM, sets a PyTorch allocator limit, and rejects CPU/disk weight placement. Other processes and allocations outside PyTorch can affect usable memory. Adjust `hardware.vram_limit_gib` to your actual allocation before running. Avoid parallel GPU jobs within this repo.

Budget roughly 150–250 GB disk for pinned model caches, several GB for token audits, and measure runtime with the smoke run. The draft's H100-hour estimates assumed 94 GB and unmeasured throughput; they are not a runtime promise for a half-memory device. The current Transformers implementation is the reference engine here.

## Commands and outputs

```bash
# Individual model jobs are resumable; these may be scheduled separately.
uv run --extra gpu wcsmatrix generate --model qwen-2b
uv run --extra gpu wcsmatrix audit --model qwen-2b

# Change scoring.top_p, scoring.modes, or scoring.word_policy in the config:
uv run wcsmatrix rescore
uv run wcsmatrix analyze

# Explicit exploratory reporting while some model jobs are still missing:
uv run wcsmatrix analyze --allow-partial
```

| Location | Contents |
| --- | --- |
| `configs/reproduction.yaml` | Pinned checkpoints, sampling, metric, and memory settings |
| `data/prompts/hc3-50.jsonl` | Frozen question IDs, prompts, and selected human answers |
| `data/texts/{human,local,frontier}.jsonl` | Text source rows and provenance |
| `results/audits/<experiment>/` | Compressed top-100 probabilities/IDs, observed tokens, offsets, full-vocabulary target mass (ignored) |
| `results/scores/<experiment>.jsonl` | Per-prompt WCS (ignored; rebuild with `rescore`) |
| `results/reports/<experiment>/` | Collection summary, matrix CSV/PNGs, bootstrap contrasts, paper comparison |
| `results/manifests/` | Machine/package preflight and API error/catalog records (ignored) |

Analysis defaults to requiring all configured scorer/source cells on every prompt. It produces human-minus-each-source contrasts, same-family-minus-cross-family contrasts excluding self cells, and paired directional asymmetry. Pointwise 95% percentile bootstrap intervals resample prompts (10,000 replicates, seed 42); they are not multiplicity-corrected. Each text's WCS is averaged equally over prompts, rather than pooling all words.

See [frontier sampling audit](docs/frontier-sampling-audit.md), [experiment extensions](docs/experiments.md), [data provenance](data/README.md), and [reproduction notes](docs/methodology.md). Code is MIT licensed; the supplied paper and upstream datasets retain their own rights.
