#!/usr/bin/env bash
set -euo pipefail

find . \( -path './.git' -o -path './.venv' \) -prune -o -type d -name '__pycache__' -exec rm -rf {} +
find . \( -path './.git' -o -path './.venv' \) -prune -o -type f \( -name '*.bak' -o -name '*.bak.*' \) -exec rm -f {} +
rm -rf snapshots validation_output tmp_validation_output .pytest_cache .metaos_runtime .metaos_runtime.bak.*
rm -f events.jsonl metrics.jsonl
rm -rf archive data state artifact_store
