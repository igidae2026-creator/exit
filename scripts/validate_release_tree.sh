#!/usr/bin/env bash
set -euo pipefail

test ! -d snapshots
find . -path "./.git" -prune -o -path "./.venv" -prune -o -type d -name "__pycache__" -exec rm -rf {} + >/dev/null 2>&1 || true
test -z "$(find . -path './.git' -prune -o -path './.venv' -prune -o -type f \( -name '*.bak' -o -name '*.bak.*' \) -print)"

python - <<'PY'
from pathlib import Path

from validation.ownership_manifest import release_paths

missing = [path for path in release_paths() if not Path(path).exists()]
if missing:
    raise SystemExit("\n".join(missing))
PY

grep -q "Deprecated Files" docs/architecture/DEPRECATED_FILES.md
