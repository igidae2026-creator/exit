from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


DEFAULT_ARCHIVE = ".metaos_runtime/archive/archive.jsonl"
DEFAULT_RESURRECTION_INDEX = ".metaos_runtime/archive/resurrection_index.jsonl"


def _archive_path() -> Path:
    path = Path(os.environ.get("METAOS_ARCHIVE", DEFAULT_ARCHIVE))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _resurrection_path() -> Path:
    path = Path(os.environ.get("METAOS_RESURRECTION_INDEX", DEFAULT_RESURRECTION_INDEX))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save(kind: str, payload: Any) -> None:
    with _archive_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"t": time.time(), "kind": kind, "payload": payload}, ensure_ascii=True) + "\n")


def remember_extinction(kind: str, payload: Any) -> None:
    with _resurrection_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"t": time.time(), "kind": kind, "payload": payload}, ensure_ascii=True) + "\n")


def load_archive() -> list[dict[str, Any]]:
    path = _archive_path()
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows

