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

required = [
    "AGENTS.md",
    "AUDIT_MANIFEST.md",
    "GENESIS_GAP_MATRIX.md",
    "ARCHITECTURE_CONTRADICTIONS.md",
    "LONG_RUN_TARGETS.md",
    "FINAL_REMEDIATION_REPORT.md",
    "docs/architecture/CANONICAL_IMPORT_GRAPH.md",
    "docs/architecture/LOOP_CANONICALIZATION.md",
    "docs/operations/LONG_RUN_TARGETS.md",
    "docs/operations/DEPRECATION_AND_COMPATIBILITY.md",
    "docs/operations/OPERATOR_QUICKSTART.md",
    "docs/runtime/STATE_MODEL.md",
    "docs/runtime/FAILURE_PROTOCOL.md",
    "docs/runtime/POLICY_RUNTIME.md",
    "docs/domains/DOMAIN_ONBOARDING.md",
]
missing_required = [path for path in required if not Path(path).exists()]
if missing_required:
    raise SystemExit("\n".join(missing_required))
PY

grep -q "Deprecated Files" docs/architecture/DEPRECATED_FILES.md
