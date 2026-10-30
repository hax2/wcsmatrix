#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== STARTING EXPERIMENT 1: SAMPLER ABLATION (configs/sampled.yaml) ==="
bash scripts/run_server.sh configs/sampled.yaml

echo "=== STARTING EXPERIMENT 2: WIKI CSAI BENCHMARK (configs/wiki.yaml) ==="
bash scripts/run_server.sh configs/wiki.yaml

echo "=== ALL NEW EXPERIMENTS COMPLETED SUCCESSFULLY ==="
