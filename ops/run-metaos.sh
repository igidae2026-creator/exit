#!/usr/bin/env bash
set -euo pipefail

ROOT="${METAOS_ROOT:-$PWD/.metaos_runtime}"
mkdir -p "$ROOT"
export METAOS_ROOT="$ROOT"
export PYTHONPATH="${PYTHONPATH:-$PWD}"

if [ -f ".venv/bin/activate" ]; then
  . .venv/bin/activate
fi

python -m app.cli run "${@}"
