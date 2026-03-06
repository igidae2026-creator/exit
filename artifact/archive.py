from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


DEFAULT_ARCHIVE = ".metaos_runtime/archive/archive.jsonl"
DEFAULT_RESURRECTION_INDEX = ".metaos_runtime/archive/resurrection_index.jsonl"


def _rooted_default(relative: str) -> Path:
    root = os.environ.get("METAOS_ROOT")
    if root:
        return Path(root) / relative
    return Path(relative)


def _archive_path() -> Path:
    path = Path(os.environ["METAOS_ARCHIVE"]) if os.environ.get("METAOS_ARCHIVE") else _rooted_default("archive/archive.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _resurrection_path() -> Path:
    if os.environ.get("METAOS_RESURRECTION_INDEX"):
        path = Path(os.environ["METAOS_RESURRECTION_INDEX"])
    else:
        path = _rooted_default("archive/resurrection_index.jsonl")
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


def seed_bank_recovery(kind: str | None = None) -> list[dict[str, Any]]:
    rows = load_archive()
    if kind is None:
        return rows
    return [row for row in rows if str(row.get("kind")) == str(kind)]


def extinction_memory() -> list[dict[str, Any]]:
    path = _resurrection_path()
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


def resurrection_replay(kind: str | None = None) -> list[dict[str, Any]]:
    rows = extinction_memory()
    if kind is None:
        return rows
    return [row for row in rows if str(row.get("kind")) == str(kind)]
