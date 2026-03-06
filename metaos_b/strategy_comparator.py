from __future__ import annotations

from typing import Any, Mapping


def compare_strategies(outcomes: Mapping[str, Mapping[str, Any]]) -> dict[str, float]:
    return {name: float((payload or {}).get("score", 0.0)) for name, payload in outcomes.items()}


__all__ = ["compare_strategies"]
