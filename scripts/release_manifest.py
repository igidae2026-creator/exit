from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MANIFEST_PATH = Path(__file__).resolve().parents[1] / "release_manifest.json"


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def release_includes() -> list[str]:
    return [str(v) for v in load_manifest().get("release_includes", [])]


def exclude_parts() -> set[str]:
    return {str(v) for v in load_manifest().get("exclude_parts", [])}


def exclude_suffixes() -> set[str]:
    return {str(v) for v in load_manifest().get("exclude_suffixes", [])}
