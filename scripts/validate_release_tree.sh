#!/usr/bin/env bash
set -euo pipefail

test ! -d snapshots
find . -path "./.git" -prune -o -path "./.venv" -prune -o -type d -name "__pycache__" -exec rm -rf {} + >/dev/null 2>&1 || true
test -z "$(find . -path './.git' -prune -o -path './.venv' -prune -o -type f \( -name '*.bak' -o -name '*.bak.*' \) -print)"

python3 - <<'PY'
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
    "docs/runtime/THRESHOLD_OPERATING_SNAPSHOT.md",
    "docs/domains/DOMAIN_ONBOARDING.md",
    "docs/ops/OPERATIONAL_AUTONOMY_STATUS.md",
]
missing_required = [path for path in required if not Path(path).exists()]
if missing_required:
    raise SystemExit("\n".join(missing_required))

runtime_status = Path("docs/runtime/CURRENT_PLATFORM_STATUS.md").read_text(encoding="utf-8")
runtime_snapshot = Path("docs/runtime/THRESHOLD_OPERATING_SNAPSHOT.md").read_text(encoding="utf-8")
ops_status = Path("docs/ops/OPERATIONAL_AUTONOMY_STATUS.md").read_text(encoding="utf-8")
ops_doc = Path("docs/ops/OPERATIONS.md").read_text(encoding="utf-8")
release_doc = Path("docs/ops/RELEASE.md").read_text(encoding="utf-8")

if "THRESHOLD_OPERATING_SNAPSHOT.md" not in runtime_status:
    raise SystemExit("docs/runtime/CURRENT_PLATFORM_STATUS.md missing THRESHOLD_OPERATING_SNAPSHOT.md reference")
if "/tmp/metaos_threshold_autonomy_clean/latest_status.json" not in runtime_snapshot:
    raise SystemExit("docs/runtime/THRESHOLD_OPERATING_SNAPSHOT.md missing live threshold source reference")
if "docs/runtime/THRESHOLD_OPERATING_SNAPSHOT.md" not in ops_status:
    raise SystemExit("docs/ops/OPERATIONAL_AUTONOMY_STATUS.md missing runtime snapshot reference")
if "OPERATIONAL_AUTONOMY_STATUS.md" not in ops_doc:
    raise SystemExit("docs/ops/OPERATIONS.md missing operational autonomy status reference")
if "OPERATIONAL_AUTONOMY_STATUS.md" not in release_doc:
    raise SystemExit("docs/ops/RELEASE.md missing operational autonomy status reference")
PY

grep -q "Deprecated Files" docs/architecture/DEPRECATED_FILES.md
