#!/usr/bin/env bash
set -euo pipefail

ROOT="${METAOS_ROOT:-$PWD/.metaos_runtime}"
find "$ROOT" -type d -name '__pycache__' -exec rm -rf {} +
find "$ROOT" -type f \( -name '*.bak' -o -name '*.tmp' \) -exec rm -f {} +
rm -rf "$ROOT/.pytest_cache" "$ROOT/tmp_validation_output" "$ROOT/validation_output"
