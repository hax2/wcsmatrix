#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${WCS_ENV_FILE:?Set WCS_ENV_FILE to the credential file outside this repository}"
uv run wcsmatrix prepare
uv run wcsmatrix frontier --env-file "$WCS_ENV_FILE" --workers 6 --max-cost-usd 20
uv run wcsmatrix analyze
