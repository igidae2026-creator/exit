from __future__ import annotations

from typing import Any, Mapping


def select_experiments(outcomes: Mapping[str, Mapping[str, Any]]) -> list[str]:
    ranked = sorted(
        outcomes.items(),
        key=lambda item: float((item[1] or {}).get("score", 0.0)),
        reverse=True,
    )
    return [name for name, _ in ranked]


__all__ = ["select_experiments"]
