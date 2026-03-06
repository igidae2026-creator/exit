#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "python3 없음"; exit 1; }
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip setuptools wheel pytest >/dev/null
mkdir -p .metaos_runtime
export METAOS_ROOT="$PWD/.metaos_runtime"
export METAOS_EVENT_LOG="$METAOS_ROOT/events.jsonl"
export METAOS_REGISTRY="$METAOS_ROOT/artifact_registry.jsonl"
export METAOS_METRICS="$METAOS_ROOT/metrics.jsonl"
export METAOS_ARCHIVE="$METAOS_ROOT/archive.jsonl"
export METAOS_CHECKPOINT="$METAOS_ROOT/checkpoint.json"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
pytest -q tests/test_oed_smoke.py
python - <<'PY'
from metaos.runtime.oed_orchestrator import step
state = step(metrics={"score":0.71,"novelty":0.28,"diversity":0.39,"cost":0.11,"fail_rate":0.02}, policy=None, workers=8, domain="default", parent=None)
print(state)
PY
