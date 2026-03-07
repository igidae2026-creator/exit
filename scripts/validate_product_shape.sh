#!/usr/bin/env bash
set -euo pipefail

test ! -d snapshots
test ! -d .metaos_runtime
test -z "$(find . -path './.git' -prune -o -path './.venv' -prune -o -type d -name '__pycache__' -print)"
test -z "$(find . -path './.git' -prune -o -path './.venv' -prune -o -type f \( -name '*.bak' -o -name '*.bak.*' \) -print)"

for path in genesis metaos_a metaos_b metaos_c artifact domains validation runtime docs tests scripts ops app; do
  test -e "$path"
done

python - <<'PY'
from pathlib import Path

pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
if 'package-dir = {"" = "src"}' in pyproject:
    raise SystemExit("fake src package-dir still present")

deprecated_roots = [Path("core"), Path("kernel"), Path("evolution"), Path("metaos/kernel"), Path("metaos/runtime"), Path("metaos/domains")]
shim_roots = {
    Path("metaos/runtime"): {
        "exploration_cycle.py",
        "exploration_economy.py",
        "exploration_loop.py",
        "knowledge_system.py",
        "lineage_ecology.py",
        "oed_orchestrator.py",
        "policy_runtime.py",
        "pressure_model.py",
        "resource_allocator.py",
        "soak_runner.py",
    },
}
for root in deprecated_roots:
    if not root.exists():
        continue
    for path in root.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8")
        if len(text.splitlines()) > 10:
            raise SystemExit(f"deprecated surface too large: {path}")
        if "Deprecated compatibility shim." not in text or "Canonical owner:" not in text:
            raise SystemExit(f"missing shim header: {path}")
PY
