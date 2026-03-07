from __future__ import annotations

from typing import Any, Mapping

from runtime.civilization_state import civilization_state as build_civilization_state
from runtime.exploration_economy import allocate_resources


def apply_economy(budgets: Mapping[str, float | int], economy: Mapping[str, Any]) -> dict[str, float | int]:
    out = dict(budgets)
    total_budget = max(float(out.get("workers", out.get("effective_workers", 0))) * 10.0, 40.0)
    attention_budget = float(economy.get("attention_budget", 0.3))
    mutation_budget = float(economy.get("mutation_budget", 0.25))
    selection_weights = dict(economy.get("selection_weights", {})) if isinstance(economy.get("selection_weights"), Mapping) else {}
    runtime_slots = dict(economy.get("runtime_slot_allocation", {})) if isinstance(economy.get("runtime_slot_allocation"), Mapping) else {}
    out["mutation_budget"] = round(min(80.0, max(8.0, total_budget * mutation_budget)), 4)
    out["domain_budget"] = round(min(60.0, max(4.0, total_budget * float(selection_weights.get("domain_genome", 0.16)))), 4)
    out["policy_budget"] = round(min(60.0, max(4.0, total_budget * float(selection_weights.get("policy", 0.16)))), 4)
    out["evaluation_budget"] = round(min(60.0, max(4.0, total_budget * float(selection_weights.get("evaluation", 0.16)))), 4)
    out["exploration_budget"] = max(2, int(round(2 + (6 * attention_budget))))
    out["runtime_slots"] = max(1, int(runtime_slots.get("runtime_slots", out.get("workers", 4))))
    out["exploration_slots"] = max(1, int(runtime_slots.get("exploration_slots", 1)))
    out["policy_budget"] = max(1, int(economy.get("policy_budget", out.get("policy_budget", 1))))
    out["evaluation_budget"] = max(1, int(economy.get("evaluation_budget", out.get("evaluation_budget", 1))))
    out["repair_budget"] = max(1, int(economy.get("repair_budget", out.get("repair_budget", 1))))
    out["domain_expansion_budget"] = max(0, int(economy.get("domain_expansion_budget", out.get("domain_expansion_budget", 0))))
    out["evaluation_diversity_budget"] = max(1, int(economy.get("evaluation_diversity_budget", out.get("evaluation_diversity_budget", 1))))
    return out


def build_economy_frame(
    stabilized_pressure: Mapping[str, float],
    ecology: Mapping[str, Any],
    population: Mapping[str, Any],
    memory_state: Mapping[str, float],
    budgets: Mapping[str, float | int],
    civilization_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    civilization_frame = dict(civilization_state or {}) if isinstance(civilization_state, Mapping) else build_civilization_state(
        state={"pressure_state": stabilized_pressure, "budgets": budgets},
    )
    economy_state = allocate_resources(
        stabilized_pressure,
        ecology,
        population,
        memory_state=memory_state,
        civilization_state=civilization_frame,
    )
    resource_allocation = {
        "attention_budget": economy_state["attention_budget"],
        "exploration_budget": economy_state["exploration_budget"],
        "mutation_budget": economy_state["mutation_budget"],
        "selection_budget": economy_state["selection_budget"],
        "policy_budget": economy_state.get("policy_budget"),
        "evaluation_budget": economy_state.get("evaluation_budget"),
        "domain_expansion_budget": economy_state.get("domain_expansion_budget"),
        "repair_budget": economy_state.get("repair_budget"),
        "diversity_allocation_budget": economy_state.get("diversity_allocation_budget"),
        "evaluation_diversity_budget": economy_state.get("evaluation_diversity_budget"),
        "selection_weights": dict(economy_state["selection_weights"]),
        "runtime_slot_allocation": dict(economy_state["runtime_slot_allocation"]),
        "memory_pressure": dict(economy_state["memory_pressure"]),
        "budget_exhausted": bool(economy_state.get("budget_exhausted", False)),
    }
    return {
        "economy": economy_state,
        "resource_allocation": resource_allocation,
        "budgets": apply_economy(budgets, economy_state),
    }


__all__ = ["apply_economy", "build_economy_frame"]
