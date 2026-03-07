from __future__ import annotations

from typing import Any, Mapping

from runtime.exploration_economy import allocate_resources


def allocate(
    pressure: Mapping[str, float],
    ecology: Mapping[str, Any],
    population: Mapping[str, Any],
    memory_state: Mapping[str, float] | None = None,
    civilization_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    allocation = allocate_resources(pressure, ecology, population, memory_state=memory_state, civilization_state=civilization_state)
    runtime_slot_allocation = dict(allocation.get("runtime_slot_allocation", {}))
    return {
        "attention_budget": allocation["attention_budget"],
        "exploration_budget": allocation["exploration_budget"],
        "mutation_budget": allocation["mutation_budget"],
        "selection_budget": allocation["selection_budget"],
        "policy_budget": allocation["policy_budget"],
        "evaluation_budget": allocation["evaluation_budget"],
        "domain_expansion_budget": allocation["domain_expansion_budget"],
        "repair_budget": allocation["repair_budget"],
        "diversity_allocation_budget": int(allocation.get("diversity_allocation_budget", 0)),
        "evaluation_diversity_budget": int(allocation.get("evaluation_diversity_budget", 0)),
        "budget_mix": dict(allocation.get("budget_mix", {})),
        "economy_balance_score": float(allocation.get("economy_balance_score", 0.0)),
        "budget_skew": float(allocation.get("budget_skew", 0.0)),
        "rebalancing_actions": list(allocation.get("rebalancing_actions", [])),
        "selection_weights": dict(allocation["selection_weights"]),
        "runtime_slots": int(runtime_slot_allocation.get("runtime_slots", 0)),
        "runtime_slot_allocation": runtime_slot_allocation,
        "memory_pressure": dict(allocation["memory_pressure"]),
        "budget_exhausted": bool(allocation.get("budget_exhausted", False)),
        "budget_remaining": int(allocation.get("budget_remaining", 0)),
        "observable": bool(allocation.get("observable", True)),
    }


__all__ = ["allocate"]
