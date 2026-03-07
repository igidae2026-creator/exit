from __future__ import annotations

from typing import Any

from runtime.civilization_memory import remember as _remember


def remember(kind: str, payload: Any) -> dict[str, Any]:
    return _remember(kind, payload)


__all__ = ["remember"]
