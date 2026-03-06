#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-$PWD}"
if [ -f ".venv/bin/activate" ]; then
  . .venv/bin/activate
fi

python -m app.cli replay-check
python -m app.cli health
python -m app.cli validate-release
