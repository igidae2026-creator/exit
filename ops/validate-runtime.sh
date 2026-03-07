#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-$PWD}"
if [ -f ".venv/bin/activate" ]; then
  . .venv/bin/activate
fi

python -m app.cli replay-check
python -m app.cli health
python -m app.cli civilization-status
python -m app.cli lineage-status
python -m app.cli domain-status
python -m app.cli economy-status
python -m app.cli stability-status
python -m app.cli safety-status
python -m app.cli long-run-check --profile "${METAOS_LONG_RUN_PROFILE:-smoke}" --ticks "${METAOS_LONG_RUN_TICKS:-2000}" --seed "${METAOS_LONG_RUN_SEED:-42}" || true
python -m app.cli validate-release
