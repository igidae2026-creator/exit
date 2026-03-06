from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping

from core.registry import read_registry


def build_lineage_view(rows: Iterable[Mapping[str, Any]]) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        artifact_id = str(row.get("artifact_id", ""))
        refs = row.get("refs", {}) if isinstance(row.get("refs"), Mapping) else {}
        parents = [str(parent) for parent in refs.get("parents", []) if parent]
        graph.setdefault(artifact_id, [])
        for parent in parents:
            graph[parent].append(artifact_id)
    return dict(graph)


def _rows(data_dir: str = "data") -> list[dict[str, Any]]:
    return [dict(row) for row in read_registry(data_dir)]


def parent_map(rows: Iterable[Mapping[str, Any]]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for row in rows:
        artifact_id = str(row.get("artifact_id", ""))
        refs = row.get("refs", {}) if isinstance(row.get("refs"), Mapping) else {}
        parents = refs.get("parents", []) if refs else row.get("parent_ids", [])
        mapping[artifact_id] = [str(parent) for parent in parents if parent]
    return mapping


def lineage_chain(artifact_id: str, rows: Iterable[Mapping[str, Any]]) -> list[str]:
    parents = parent_map(rows)
    chain: list[str] = []
    current = str(artifact_id)
    seen: set[str] = set()
    while current and current not in seen:
        chain.append(current)
        seen.add(current)
        lineage_parents = parents.get(current, [])
        current = lineage_parents[0] if lineage_parents else ""
    return chain


def lineage_graph(data_dir: str = "data") -> dict[str, list[str]]:
    return build_lineage_view(_rows(data_dir))


def lineage_counts(data_dir: str = "data") -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in _rows(data_dir):
        metadata = row.get("metadata") if isinstance(row.get("metadata"), Mapping) else {}
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
