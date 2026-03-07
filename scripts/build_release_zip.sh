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

from scripts.release_manifest import exclude_parts, exclude_suffixes, release_includes

zip_path = Path(sys.argv[1])
root = Path('.').resolve()
include_roots = release_includes()
parts_excluded = exclude_parts()
suffixes_excluded = exclude_suffixes()
with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    for item in include_roots:
        path = root / item
        if not path.exists():
            continue
        if path.is_file():
            zf.write(path, path.relative_to(root))
            continue
        for child in path.rglob('*'):
            rel = child.relative_to(root)
            if any(part in parts_excluded for part in rel.parts):
                continue
            if child.suffix in suffixes_excluded or child.name.endswith('.bak'):
                continue
            if child.is_file():
                zf.write(child, rel)
print(zip_path)
PY
