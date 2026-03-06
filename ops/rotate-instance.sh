#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INST="${1:-A}"

BASE="$ROOT/instances/$INST"
mkdir -p "$BASE/state" "$BASE/logs/archive" "$BASE/artifact_store"

# Ensure clean link targets for code/domain snapshots.
rm -rf "$BASE/core" "$BASE/domains"
ln -s "$ROOT/core" "$BASE/core"
ln -s "$ROOT/domains" "$BASE/domains"

# 인스턴스별 runtime 파일은 분리
touch "$BASE/metrics.jsonl" "$BASE/events.jsonl"

echo "INSTANCE=$INST"
echo "PATH=$BASE"
echo "Run: cd \"$BASE\" && python3 -m core.autonomous_daemon"
