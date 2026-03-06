from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from artifact.archive import load_archive
from artifact.civilization_registry import civilization_state as artifact_civilization_state


def _memory_path() -> Path:
    root = os.environ.get("METAOS_ROOT")
    if os.environ.get("METAOS_CIVILIZATION_MEMORY"):
        return Path(os.environ["METAOS_CIVILIZATION_MEMORY"])
    if root:
        return Path(root) / "archive" / "civilization_memory.jsonl"
    return Path(".metaos_runtime/archive/civilization_memory.jsonl")


def _memory_rows() -> list[dict[str, Any]]:
    path = _memory_path()
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


def civilization_state() -> dict[str, Any]:
    archive_rows = load_archive()
    memory_rows = _memory_rows()
    if os.environ.get("METAOS_ROOT") or os.environ.get("METAOS_REGISTRY"):
        artifact_state = artifact_civilization_state()
    else:
        artifact_state = {
            "artifact_counts": {},
            "domain_counts": {},
            "lineage_counts": {},
            "policy_generations": 0,
        }
    artifact_distribution = dict(artifact_state.get("artifact_counts", {}))
    domain_distribution = dict(artifact_state.get("domain_counts", {}))
    lineage_graph = dict(artifact_state.get("lineage_counts", {}))
    archive_kinds = {str(row.get("kind", "")) for row in archive_rows if row.get("kind")}
    memory_kinds = {str(row.get("kind", "")) for row in memory_rows if row.get("kind")}
    density_base = len(archive_kinds | memory_kinds) + len(domain_distribution) + len(artifact_distribution)
    total_rows = len(archive_rows) + len(memory_rows)
    return {
        "knowledge_density": round(min(1.0, density_base / 24.0), 4),
        "memory_growth": round(min(1.0, total_rows / 720.0), 4),
        "artifact_distribution": artifact_distribution,
        "domain_distribution": domain_distribution,
        "policy_evolution": int(artifact_state.get("policy_generations", 0)),
        "lineage_graph": lineage_graph,
        "exploration_outcomes": {
            "archived_rows": len(archive_rows),
            "memory_rows": len(memory_rows),
            "outcome_kinds": sorted(kind for kind in archive_kinds if kind),
        },
    }


__all__ = ["civilization_state"]
