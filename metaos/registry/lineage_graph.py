from __future__ import annotations

import collections
import json
import os
from pathlib import Path


def _registry_path() -> Path:
    root = os.environ.get("METAOS_ROOT")
    if os.environ.get("METAOS_REGISTRY"):
        return Path(os.environ["METAOS_REGISTRY"])
    if root:
        return Path(root) / "artifact_registry.jsonl"
    return Path(".metaos_runtime/data/artifact_registry.jsonl")


def load() -> collections.defaultdict[str, list[str]]:
    graph: collections.defaultdict[str, list[str]] = collections.defaultdict(list)
    path = _registry_path()
    if not path.exists():
        return graph
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
                parent = row.get("parent")
                if parent:
                    graph[str(parent)].append(str(row["id"]))
            except Exception:
                pass
    return graph


def concentration() -> float:
    graph = load()
    if not graph:
        return 0.0
    counts = sorted((len(values) for values in graph.values()), reverse=True)
    top = counts[0]
    total = sum(counts) or 1
    return top / total
