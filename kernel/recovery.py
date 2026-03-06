from __future__ import annotations

from typing import Any, Callable


def retry_once(fn: Callable[[], Any]) -> tuple[Any, bool]:
    try:
        return fn(), False
    except Exception:
        return fn(), True


def rollback(state: Any, fallback: Any) -> Any:
    return fallback if fallback is not None else state


def safe_mode(state: Any) -> dict[str, Any]:
    return {"mode": "safe_mode", "state": state}

