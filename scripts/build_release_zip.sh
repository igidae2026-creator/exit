#!/usr/bin/env bash
set -euo pipefail

out_dir="dist"
mkdir -p "$out_dir"
stamp="$(date +%Y%m%d_%H%M%S)"
zip_path="$out_dir/metaos_release_${stamp}.zip"

python - <<'PY' "$zip_path"
import sys
import zipfile
from pathlib import Path

zip_path = Path(sys.argv[1])
root = Path(".").resolve()
include_roots = [
    "genesis",
    "metaos_a",
    "metaos_b",
    "metaos_c",
    "artifact",
    "domains",
    "validation",
    "runtime",
    "app",
    "metaos",
    "observer",
    "signal",
    "strategy",
    "ecosystem",
    "federation",
    "evolution",
    "core",
    "kernel",
    "loop",
    "docs",
    "tests",
    "ops",
    "scripts",
    "README.md",
    "RUNBOOK.md",
    "pyproject.toml",
    "setup.py",
]
exclude_parts = {"__pycache__", "snapshots", ".git", ".venv", "dist"}
exclude_suffixes = {".bak", ".pyc"}
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for item in include_roots:
        path = root / item
        if not path.exists():
            continue
        if path.is_file():
            zf.write(path, path.relative_to(root))
            continue
        for child in path.rglob("*"):
            rel = child.relative_to(root)
            if any(part in exclude_parts for part in rel.parts):
                continue
            if child.suffix in exclude_suffixes or child.name.endswith(".bak"):
                continue
            if child.is_file():
                zf.write(child, rel)
print(zip_path)
PY
