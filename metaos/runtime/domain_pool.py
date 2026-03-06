from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping


DEFAULT_DOMAIN_POOL = ".metaos_runtime/domain_pool.json"


def _pool_path() -> Path:
    path = Path(os.environ.get("METAOS_DOMAIN_POOL", DEFAULT_DOMAIN_POOL))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load() -> dict[str, dict[str, Any]]:
    path = _pool_path()
    if not path.exists():
        return {"default": {"name": "default", "genome": None}}
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        return {"default": {"name": "default", "genome": None}}
    if isinstance(payload, dict) and payload:
        return {str(key): dict(value) if isinstance(value, Mapping) else {"name": str(key), "genome": value} for key, value in payload.items()}
    return {"default": {"name": "default", "genome": None}}


def _save(pool: Mapping[str, Any]) -> None:
    with _pool_path().open("w", encoding="utf-8") as handle:
        json.dump(dict(pool), handle, ensure_ascii=True)


def register_domain(name: str, genome: Mapping[str, Any] | None = None) -> dict[str, Any]:
    pool = _load()
    pool[str(name)] = {"name": str(name), "genome": dict(genome) if isinstance(genome, Mapping) else genome}
    _save(pool)
    return dict(pool[str(name)])


def list_domains() -> list[str]:
    return sorted(_load())


def get_domain(name: str) -> dict[str, Any] | None:
    return _load().get(str(name))
