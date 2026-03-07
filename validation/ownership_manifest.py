from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_DEFAULT_PATH = Path(__file__).with_name("ownership_manifest.json")


def load_ownership_manifest(path: str | Path | None = None) -> dict[str, Any]:
    manifest_path = Path(path) if path is not None else _DEFAULT_PATH
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def ownership_rows(path: str | Path | None = None) -> list[dict[str, Any]]:
    manifest = load_ownership_manifest(path)
    return [dict(row) for row in manifest.get("paths", []) if isinstance(row, dict)]


def release_paths(path: str | Path | None = None) -> list[str]:
    return [str(row["path"]) for row in ownership_rows(path) if bool(row.get("release_included"))]


def packaged_roots(path: str | Path | None = None) -> list[str]:
    return [str(row["path"]) for row in ownership_rows(path) if bool(row.get("packaged"))]


def public_paths(path: str | Path | None = None) -> list[str]:
    return [str(row["path"]) for row in ownership_rows(path) if bool(row.get("public"))]


__all__ = ["load_ownership_manifest", "ownership_rows", "packaged_roots", "public_paths", "release_paths"]
