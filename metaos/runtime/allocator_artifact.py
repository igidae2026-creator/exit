from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Mapping

from artifact.registry import register_envelope


DEFAULT_ALLOCATOR_REGISTRY = ".metaos_runtime/data/allocator_registry.jsonl"


def _registry_path() -> Path:
    root = os.environ.get("METAOS_ROOT")
    if os.environ.get("METAOS_ALLOCATOR_REGISTRY"):
        path = Path(os.environ["METAOS_ALLOCATOR_REGISTRY"])
    elif root:
        path = Path(root) / "allocator_registry.jsonl"
    else:
        path = Path(DEFAULT_ALLOCATOR_REGISTRY)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def register_allocator_artifact(
    allocator: Mapping[str, Any],
    pressure: Mapping[str, float],
    workers: int,
    budgets: Mapping[str, float],
    *,
    parent: str | None = None,
) -> str:
    artifact_id = register_envelope(
        aclass="allocator",
        atype="allocator",
        spec={"allocator": dict(allocator)},
        refs={"parents": [parent] if parent else [], "inputs": [], "subjects": [], "context": {"quota": dict(budgets)}},
        provenance={"pressure": dict(pressure), "workers": int(workers)},
    )
    rec = {
        "id": artifact_id,
        "parent": parent,
        "allocator": dict(allocator),
        "pressure": dict(pressure),
        "workers": int(workers),
        "budgets": dict(budgets),
        "t": time.time(),
    }
    with _registry_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    return artifact_id


def load_all() -> list[dict[str, Any]]:
    path = _registry_path()
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
