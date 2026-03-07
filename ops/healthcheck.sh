#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-$PWD}"
if [ -f ".venv/bin/activate" ]; then
  . .venv/bin/activate
fi

python -m app.cli replay-check >/dev/null
python -m app.cli health >/dev/null
python -m app.cli civilization-status >/dev/null
python -m app.cli lineage-status >/dev/null
python -m app.cli domain-status >/dev/null
python -m app.cli economy-status >/dev/null
python -m app.cli stability-status >/dev/null
python -m app.cli safety-status >/dev/null
