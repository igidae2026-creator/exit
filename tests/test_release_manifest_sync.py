from __future__ import annotations

import json
from pathlib import Path


def _manifest() -> dict[str, object]:
    return json.loads(Path("release_manifest.json").read_text(encoding="utf-8"))


def test_manifest_includes_required_runtime_and_release_paths() -> None:
    include = set(_manifest()["release_includes"])
    for required in (
        "app",
        "artifact",
        "domains",
        "docs",
        "genesis",
        "metaos",
        "metaos_a",
        "metaos_b",
        "metaos_c",
        "observer",
        "runtime",
        "scripts",
        "tests",
        "validation",
        "README.md",
        "RUNBOOK.md",
    ):
        assert required in include


def test_manifest_and_ownership_rows_are_consistent() -> None:
    manifest = _manifest()
    include = set(manifest["release_includes"])
    ownership = manifest["ownership"]
    assert ownership
    for row in ownership:
        path = row["path"]
        included = bool(row["release_included"])
        if included:
            assert path in include


def test_release_scripts_read_manifest() -> None:
    build_script = Path("scripts/build_release_zip.sh").read_text(encoding="utf-8")
    validate_script = Path("scripts/validate_release_tree.sh").read_text(encoding="utf-8")
    assert "scripts.release_manifest" in build_script
    assert "scripts.release_manifest" in validate_script
