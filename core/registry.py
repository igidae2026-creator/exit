from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.event_log import append_jsonl, ensure_spine, read_registry as _read_registry


def register_artifact(record: Mapping[str, Any], data_dir: str = "data") -> dict[str, Any]:
    payload = dict(record)
    payload.setdefault("parent_ids", [])
    payload.setdefault("metadata", {})
    payload.setdefault("payload", {})
    append_jsonl(ensure_spine(data_dir).registry_path, payload)
    return payload


def read_registry(data_dir: str = "data") -> Iterable[dict[str, Any]]:
    return _read_registry(data_dir)


def lineage_for(artifact_id: str, data_dir: str = "data") -> list[dict[str, Any]]:
    rows = [row for row in read_registry(data_dir) if row.get("artifact_id") == artifact_id]
    if rows:
        return rows

    parents: list[dict[str, Any]] = []
    for row in read_registry(data_dir):
        if artifact_id in row.get("parent_ids", []):
            parents.append(row)
    return parents
