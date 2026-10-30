#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
config="${1:-configs/reproduction.yaml}"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
export TOKENIZERS_PARALLELISM=false
uv run --extra gpu wcsmatrix --config "$config" preflight
uv run --extra gpu wcsmatrix --config "$config" generate
uv run --extra gpu wcsmatrix --config "$config" audit
uv run wcsmatrix --config "$config" analyze --allow-partial
