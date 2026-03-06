from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any


DEFAULT_REGISTRY = ".metaos_runtime/data/artifact_registry.jsonl"


def _registry_path() -> Path:
    path = Path(os.environ.get("METAOS_REGISTRY", DEFAULT_REGISTRY))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def register(
    data: Any,
    parent: str | None = None,
    atype: str = "strategy",
    score: float = 0.0,
    novelty: float = 0.0,
    diversity: float = 0.0,
    cost: float = 0.0,
    quest: Any = None,
    policy: Any = None,
) -> str:
    rec = {
        "id": str(uuid.uuid4()),
        "type": atype,
        "parent": parent,
        "data": data,
        "score": score,
        "novelty": novelty,
        "diversity": diversity,
        "cost": cost,
        "quest": quest,
        "policy": policy,
        "t": time.time(),
    }
    with _registry_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    return str(rec["id"])
