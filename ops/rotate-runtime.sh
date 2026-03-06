#!/usr/bin/env bash
set -euo pipefail

ROOT="${METAOS_ROOT:-$PWD/.metaos_runtime}"
ROTATIONS="$ROOT/rotations"
MANIFEST="$ROTATIONS/manifest.jsonl"
mkdir -p "$ROTATIONS"

stamp="$(date +%Y%m%d_%H%M%S)"
for path in "$ROOT/events.jsonl" "$ROOT/metrics.jsonl" "$ROOT/artifact_registry.jsonl" "$ROOT/archive/archive.jsonl"; do
  [ -f "$path" ] || continue
  size="$(wc -c < "$path")"
  if [ "$size" -lt 1048576 ]; then
    continue
  fi
  target="$ROTATIONS/$(basename "$path").$stamp"
  cp "$path" "$target"
  python - <<'PY' "$MANIFEST" "$path" "$target" "$size"
import json, sys, time
manifest, source, target, size = sys.argv[1:]
with open(manifest, "a", encoding="utf-8") as handle:
    handle.write(json.dumps({"t": time.time(), "source": source, "target": target, "size": int(size)}) + "\n")
PY
done
