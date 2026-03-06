from __future__ import annotations

from typing import Any, Mapping

from metaos_b.experiment_selector import select_experiments
from metaos_b.manager_state import ManagerState
from metaos_b.resource_allocator import allocate_for_units
from metaos_b.strategy_comparator import compare_strategies


def schedule(
    pressure: Mapping[str, float],
    artifact_outcomes: Mapping[str, Mapping[str, Any]],
    ecology: Mapping[str, Any],
    civilization_state: Mapping[str, Any],
) -> dict[str, Any]:
    domain_names = list(artifact_outcomes) or list((civilization_state.get("domains", {}) if isinstance(civilization_state.get("domains"), Mapping) else {})) or ["code"]
    allocation = allocate_for_units(pressure, ecology, {"population_counts": {}}, domain_names)
    ranking = select_experiments(artifact_outcomes)
    comparison = compare_strategies(artifact_outcomes)
    state = ManagerState(
        tick=int(civilization_state.get("tick", 0) or 0),
        runtime_slots=dict(allocation["per_unit_slots"]),
        exploration_budgets=dict(allocation["per_unit_budget"]),
        selected_experiments=list(ranking),
    )
    return {
        "manager_state": state,
        "runtime_slots": dict(allocation["per_unit_slots"]),
        "exploration_budgets": dict(allocation["per_unit_budget"]),
        "selected_experiments": list(ranking),
        "strategy_scores": comparison,
    }


__all__ = ["schedule"]
