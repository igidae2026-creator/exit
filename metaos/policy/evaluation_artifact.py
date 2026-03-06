from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Mapping

from artifact.registry import register_envelope


DEFAULT_EVALUATION_REGISTRY = ".metaos_runtime/data/evaluation_artifacts.jsonl"


def _registry_path() -> Path:
    root = os.environ.get("METAOS_ROOT")
    if os.environ.get("METAOS_EVALUATION_REGISTRY"):
        path = Path(os.environ["METAOS_EVALUATION_REGISTRY"])
    elif root:
        path = Path(root) / "evaluation_artifacts.jsonl"
    else:
        path = Path(DEFAULT_EVALUATION_REGISTRY)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def register_evaluation(
    evaluation: Mapping[str, Any],
    pressure: Mapping[str, float],
    score: float,
    *,
    parent: str | None = None,
) -> str:
    artifact_id = register_envelope(
        aclass="evaluation",
        atype="evaluation_policy",
        spec={"evaluation": dict(evaluation)},
        refs={"parents": [parent] if parent else [], "inputs": [], "subjects": [], "context": {}},
        provenance={"pressure": dict(pressure), "score": float(score)},
    )
    rec = {
        "id": artifact_id,
        "parent": parent,
        "evaluation": dict(evaluation),
        "pressure": dict(pressure),
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
