from __future__ import annotations

from typing import Any, Mapping


def generate_strategies(manager_output: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "strategy_lineage": list(manager_output.get("selected_experiments", [])),
        "strategy_scores": dict(manager_output.get("strategy_scores", {})),
    }


__all__ = ["generate_strategies"]
