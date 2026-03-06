#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-$PWD}"
if [ -f ".venv/bin/activate" ]; then
  . .venv/bin/activate
fi

python -m app.cli replay-check >/dev/null
python -m app.cli health >/dev/null
