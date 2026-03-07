#!/usr/bin/env bash
set -euo pipefail

test ! -d snapshots
find . -path "./.git" -prune -o -path "./.venv" -prune -o -type d -name "__pycache__" -exec rm -rf {} + >/dev/null 2>&1 || true
test -z "$(find . -path './.git' -prune -o -path './.venv' -prune -o -type f \( -name '*.bak' -o -name '*.bak.*' \) -print)"

for path in genesis metaos_a metaos_b metaos_c artifact domains validation runtime app metaos observer signal strategy ecosystem federation evolution core kernel loop docs tests ops scripts README.md RUNBOOK.md pyproject.toml setup.py; do
  test -e "$path"
done

grep -q "Deprecated Files" docs/architecture/DEPRECATED_FILES.md
