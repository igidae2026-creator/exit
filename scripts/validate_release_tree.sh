#!/usr/bin/env bash
set -euo pipefail

test ! -d snapshots
test -z "$(find . -path './.git' -prune -o -path './.venv' -prune -o -type d -name '__pycache__' -print)"
test -z "$(find . -path './.git' -prune -o -path './.venv' -prune -o -type f \( -name '*.bak' -o -name '*.bak.*' \) -print)"

for path in genesis metaos_a metaos_b metaos_c artifact domains validation runtime docs tests ops scripts README.md RUNBOOK.md; do
  test -e "$path"
done

grep -q "Deprecated Files" docs/architecture/DEPRECATED_FILES.md
