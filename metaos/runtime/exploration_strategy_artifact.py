from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Mapping

from artifact.registry import register_envelope


DEFAULT_STRATEGY_REGISTRY = ".metaos_runtime/data/exploration_strategy_artifacts.jsonl"


def _registry_path() -> Path:
    path = Path(os.environ.get("METAOS_EXPLORATION_STRATEGY_REGISTRY", DEFAULT_STRATEGY_REGISTRY))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def register_strategy(
    strategy: Mapping[str, Any],
    pressure: Mapping[str, float],
    market: Mapping[str, float],
    score: float,
    *,
    parent: str | None = None,
) -> str:
    artifact_id = register_envelope(
        aclass="strategy",
        atype="exploration_strategy",
        spec={"strategy": dict(strategy)},
        refs={"parents": [parent] if parent else [], "inputs": [], "subjects": [], "context": {}},
        provenance={"pressure": dict(pressure), "market": dict(market), "score": float(score)},
    )
    rec = {
        "id": artifact_id,
        "parent": parent,
        "strategy": dict(strategy),
        "pressure": dict(pressure),
        "market": dict(market),
        "score": float(score),
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
