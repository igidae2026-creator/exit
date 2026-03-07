from __future__ import annotations

import os
from typing import Any, Callable


def retry_once(fn: Callable[[], Any]) -> tuple[Any, bool]:
    try:
        return fn(), False
    except Exception:
        return fn(), True


def rollback(state: Any, fallback: Any) -> Any:
    return fallback if fallback is not None else state


def replay_restore(default: Any = None) -> Any:
    from genesis.replay import replay_state

    if not any(os.environ.get(name) for name in ("METAOS_EVENT_LOG", "METAOS_METRICS", "METAOS_REGISTRY", "METAOS_ARCHIVE")):
        return default
    restored = replay_state()
    if not restored or (restored.get("events", 0) == 0 and restored.get("metrics", 0) == 0 and restored.get("artifacts", 0) == 0):
        return default
    return restored


def safe_mode(state: Any) -> dict[str, Any]:
    return {"mode": "safe_mode", "state": state}
