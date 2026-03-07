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
python -m app.cli pressure-status
python -m app.cli economy-status
python -m app.cli stability-status
python -m app.cli safety-status
python -m app.cli long-run-check --tier "${METAOS_LONG_RUN_TIER:-smoke}" --ticks "${METAOS_LONG_RUN_TICKS:-256}" --seed "${METAOS_LONG_RUN_SEED:-42}"
python -m app.cli validate-release
