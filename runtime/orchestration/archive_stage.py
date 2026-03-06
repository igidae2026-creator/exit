from __future__ import annotations

from typing import Any, Callable, Mapping


def persist_runtime_frames(save_fn: Callable[[str, Any], None], remember_fn: Callable[[str, Any], None], payload: Mapping[str, Any]) -> None:
    for key in (
        "pressure",
        "stabilized_pressure",
        "quest",
        "policy",
        "policy_stack",
        "evaluation",
        "ecology",
        "guard",
        "stabilized_market",
        "strategy_of_strategy",
        "civilization_selection",
        "population",
        "governance",
        "economy",
        "cooldown",
        "meta_exploration",
        "exploration_cycle",
        "genome",
        "resource_allocation",
        "exploration_economy_state",
        "civilization_state",
        "civilization_stability",
    ):
        if key in payload:
            save_fn(key, payload[key])
    if payload.get("repair"):
        save_fn("repair", payload["repair"])
        remember_fn("repair_artifact", payload["repair"])
    remember_map = {
        "pressure_snapshot": payload.get("stabilized_pressure"),
        "population_snapshot": payload.get("population"),
        "governance_snapshot": payload.get("governance"),
        "economy_snapshot": payload.get("economy"),
        "meta_exploration_artifact": payload.get("meta_exploration"),
        "exploration_cycle": payload.get("exploration_cycle"),
        "resource_allocation": payload.get("resource_allocation"),
        "exploration_economy_state": payload.get("exploration_economy_state"),
        "civilization_state": payload.get("civilization_state"),
        "civilization_stability": payload.get("civilization_stability"),
    }
    for key, value in remember_map.items():
        if value is not None:
            remember_fn(key, value)


__all__ = ["persist_runtime_frames"]
