from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.event_log import append_jsonl, ensure_spine, read_registry as _read_registry


def _normalize(row: Mapping[str, Any]) -> dict[str, Any]:
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else None
    if payload and "artifact_id" in payload and "artifact_id" not in row:
        normalized = dict(payload)
        normalized.setdefault("timestamp", row.get("timestamp"))
        return normalized
    return dict(row)


def register_artifact(record: Mapping[str, Any], data_dir: str = "data") -> dict[str, Any]:
    payload = dict(record)
    payload.setdefault("parent_ids", [])
    payload.setdefault("metadata", {})
    payload.setdefault("payload", {})
    append_jsonl(ensure_spine(data_dir).registry_path, payload)
    return payload


def read_registry(data_dir: str = "data") -> Iterable[dict[str, Any]]:
    rows = [_normalize(row) for row in _read_registry(data_dir)]
    by_id: dict[str, dict[str, Any]] = {}
    ordered: list[str] = []
    for row in rows:
        artifact_id = str(row.get("artifact_id") or "")
        if not artifact_id:
            continue
        score = (1 if row.get("kind") else 0) + (1 if row.get("payload") else 0)
        current = by_id.get(artifact_id)
        current_score = ((1 if current.get("kind") else 0) + (1 if current.get("payload") else 0)) if current else -1
        if artifact_id not in by_id:
            ordered.append(artifact_id)
        if current is None or score >= current_score:
            by_id[artifact_id] = row
    return [by_id[artifact_id] for artifact_id in ordered]


def lineage_for(artifact_id: str, data_dir: str = "data") -> list[dict[str, Any]]:
    rows = [row for row in read_registry(data_dir) if row.get("artifact_id") == artifact_id]
    if rows:
        return rows
    parents: list[dict[str, Any]] = []
    for row in read_registry(data_dir):
        if artifact_id in row.get("parent_ids", []):
            parents.append(row)
    return parents
