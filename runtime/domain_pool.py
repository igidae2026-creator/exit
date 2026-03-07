from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Mapping


DEFAULT_DOMAIN_POOL = ".metaos_runtime/domain_pool.json"
_SEED_DOMAINS = {
    "default": {"name": "default", "genome": {"name": "default", "constraints": {}, "evaluation_recipe": {"score": 1.0}, "mutation_priors": {"mutation_rate": 0.2}}},
    "default_variant": {
        "name": "default_variant",
        "genome": {"name": "default_variant", "constraints": {"stability": 0.6}, "evaluation_recipe": {"score": 0.96}, "mutation_priors": {"mutation_rate": 0.24}},
    },
    "exploration_variant": {
        "name": "exploration_variant",
        "genome": {"name": "exploration_variant", "constraints": {"novelty": 0.7}, "evaluation_recipe": {"score": 0.92}, "mutation_priors": {"mutation_rate": 0.28}},
    },
}


def _pool_path() -> Path:
    root = os.environ.get("METAOS_ROOT")
    if os.environ.get("METAOS_DOMAIN_POOL"):
        path = Path(os.environ["METAOS_DOMAIN_POOL"])
    elif root:
        path = Path(root) / "domain_pool.json"
    else:
        path = Path(DEFAULT_DOMAIN_POOL)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _normalize_domain(name: str, value: Any) -> dict[str, Any]:
    payload = dict(value) if isinstance(value, Mapping) else {"genome": value}
    genome = dict(payload.get("genome", {})) if isinstance(payload.get("genome"), Mapping) else {"name": str(name)}
    return {
        "name": str(name),
        "genome": genome,
        "active": bool(payload.get("active", True)),
        "created_at": float(payload.get("created_at", time.time())),
        "created_by": str(payload.get("created_by", "runtime")),
    }


def _load() -> dict[str, dict[str, Any]]:
    path = _pool_path()
    if not path.exists():
        return {key: _normalize_domain(key, value) for key, value in _SEED_DOMAINS.items()}
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        return {key: _normalize_domain(key, value) for key, value in _SEED_DOMAINS.items()}
    if isinstance(payload, dict) and payload:
        out = {str(key): _normalize_domain(str(key), value) for key, value in payload.items()}
        for key, value in _SEED_DOMAINS.items():
            out.setdefault(key, _normalize_domain(key, value))
        return out
    return {key: _normalize_domain(key, value) for key, value in _SEED_DOMAINS.items()}


def _save(pool: Mapping[str, Any]) -> None:
    with _pool_path().open("w", encoding="utf-8") as handle:
        json.dump(dict(pool), handle, ensure_ascii=True)


def register_domain(name: str, genome: Mapping[str, Any] | None = None) -> dict[str, Any]:
    pool = _load()
    existing = dict(pool.get(str(name), {}))
    pool[str(name)] = _normalize_domain(
        str(name),
        {
            **existing,
            "name": str(name),
            "genome": dict(genome) if isinstance(genome, Mapping) else existing.get("genome", {"name": str(name)}),
            "active": True,
            "created_at": existing.get("created_at", time.time()),
        },
    )
    _save(pool)
    return dict(pool[str(name)])


def ensure_seed_domains() -> dict[str, dict[str, Any]]:
    pool = _load()
    changed = False
    for key, value in _SEED_DOMAINS.items():
        if key not in pool:
            pool[key] = _normalize_domain(key, value)
            changed = True
    if changed:
        _save(pool)
    return pool


def domain_names() -> list[str]:
    return sorted(ensure_seed_domains())


def list_domains() -> list[str]:
    return domain_names()


def get_domain(name: str) -> dict[str, Any] | None:
    return ensure_seed_domains().get(str(name))


def domain_snapshot() -> dict[str, Any]:
    pool = ensure_seed_domains()
    active = sorted(name for name, payload in pool.items() if bool(payload.get("active", True)))
    created = sorted(pool)
    return {
        "created_domains": created,
        "active_domains": active,
        "domain_count": len(created),
        "active_domain_count": len(active),
        "domains": pool,
    }


__all__ = [
    "domain_names",
    "domain_snapshot",
    "ensure_seed_domains",
    "get_domain",
    "list_domains",
    "register_domain",
]
