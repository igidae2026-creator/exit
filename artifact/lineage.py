from __future__ import annotations

from typing import Any

from core.registry import read_registry


def parent_map(data_dir: str = "data") -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for row in read_registry(data_dir):
        artifact_id = str(row.get("artifact_id") or "")
        if not artifact_id:
            continue
        mapping[artifact_id] = [str(parent) for parent in row.get("parent_ids", [])]
    return mapping


def lineage_chain(artifact_id: str, data_dir: str = "data") -> list[dict[str, Any]]:
    by_id = {
        str(row.get("artifact_id") or ""): row
        for row in read_registry(data_dir)
        if row.get("artifact_id")
    }
    chain: list[dict[str, Any]] = []
    current = artifact_id
    seen: set[str] = set()
    while current and current not in seen and current in by_id:
        row = by_id[current]
        chain.append(row)
        seen.add(current)
        parents = row.get("parent_ids", [])
        current = str(parents[0]) if parents else ""
    return chain


def lineage_concentration(data_dir: str = "data") -> float:
    mapping = parent_map(data_dir)
    if not mapping:
        return 0.0
    child_counts: dict[str, int] = {}
    for parents in mapping.values():
        for parent_id in parents:
            child_counts[parent_id] = child_counts.get(parent_id, 0) + 1
    if not child_counts:
        return 0.0
    max_children = max(child_counts.values())
    return max_children / max(1, len(mapping))
