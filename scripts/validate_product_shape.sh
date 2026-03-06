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

deprecated_roots = [Path("kernel"), Path("evolution"), Path("metaos/kernel"), Path("metaos/runtime")]
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
    },
}
for root in deprecated_roots:
    if not root.exists():
        continue
    for path in root.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8")
        if len(text.splitlines()) > 220:
            raise SystemExit(f"deprecated surface too large: {path}")
        shim_names = shim_roots.get(root)
        if shim_names and path.name in shim_names and "Deprecated compatibility shim. Canonical owner:" not in text:
            raise SystemExit(f"missing shim header: {path}")
PY
