from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from core.registry import read_registry


def _rows(data_dir: str = "data") -> list[dict[str, Any]]:
    return [dict(row) for row in read_registry(data_dir)]


def parent_map(data_dir: str = "data") -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for row in _rows(data_dir):
        artifact_id = str(row.get("artifact_id") or "")
        if artifact_id:
            mapping[artifact_id] = [str(parent) for parent in row.get("parent_ids", []) if parent]
    return mapping


def lineage_chain(artifact_id: str, data_dir: str = "data") -> list[dict[str, Any]]:
    by_id = {str(row.get("artifact_id") or ""): row for row in _rows(data_dir) if row.get("artifact_id")}
    chain: list[dict[str, Any]] = []
    current = artifact_id
    seen: set[str] = set()
    while current and current not in seen and current in by_id:
        row = by_id[current]
        chain.append(row)
        seen.add(current)
        parents = [str(parent) for parent in row.get("parent_ids", []) if parent]
        current = parents[0] if parents else ""
    return chain


def lineage_roots(data_dir: str = "data") -> dict[str, str]:
    roots: dict[str, str] = {}
    for artifact_id in parent_map(data_dir):
        chain = lineage_chain(artifact_id, data_dir)
        roots[artifact_id] = str(chain[-1].get("artifact_id")) if chain else artifact_id
    return roots


def lineage_graph(data_dir: str = "data") -> dict[str, list[str]]:
    graph: dict[str, list[str]] = defaultdict(list)
    for artifact_id, parents in parent_map(data_dir).items():
        if not parents:
            graph.setdefault(artifact_id, [])
            continue
        for parent in parents:
            graph[parent].append(artifact_id)
    return dict(graph)


def lineage_counts(data_dir: str = "data") -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in _rows(data_dir):
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        lineage_id = str(metadata.get("lineage_id") or row.get("artifact_id") or "root")
        counts[lineage_id] += 1
    return dict(counts)


def dominant_lineage(data_dir: str = "data") -> tuple[str, int]:
    counts = lineage_counts(data_dir)
    if not counts:
        return "", 0
    lineage_id = max(counts, key=counts.get)
    return lineage_id, counts[lineage_id]


def lineage_concentration(data_dir: str = "data") -> float:
    counts = lineage_counts(data_dir)
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    return max(counts.values()) / total
