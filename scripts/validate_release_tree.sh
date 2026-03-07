#!/usr/bin/env bash
set -euo pipefail

python - <<'PY'
from pathlib import Path

from scripts.release_manifest import exclude_parts, release_includes

root = Path('.')
for path in release_includes():
    if not (root / path).exists():
        raise SystemExit(f"missing required release path: {path}")

blocked_roots = {'.git', '.venv', 'dist', 'snapshots'}
for blocked in blocked_roots:
    if (root / blocked).exists() and blocked == 'snapshots':
        raise SystemExit('snapshots directory must not exist in release tree')

excluded = exclude_parts()
for p in root.rglob('*'):
    if '__pycache__' in p.parts:
        # generated cache files are ignored by release builder
        continue
    if p.is_file() and (p.suffix == '.pyc' or p.name.endswith('.bak') or '.bak.' in p.name):
        raise SystemExit(f'disallowed file in release tree: {p}')

deprecated_doc = root / 'docs/architecture/DEPRECATED_FILES.md'
if 'Deprecated Files' not in deprecated_doc.read_text(encoding='utf-8'):
    raise SystemExit('missing deprecated files heading')
PY
