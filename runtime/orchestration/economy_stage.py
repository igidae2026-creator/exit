from __future__ import annotations

from typing import Any, Mapping

from runtime.exploration_economy import exploration_economy


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
    return out


def build_economy_frame(
    stabilized_pressure: Mapping[str, float],
    ecology: Mapping[str, Any],
    population: Mapping[str, Any],
    memory_state: Mapping[str, float],
    budgets: Mapping[str, float | int],
) -> dict[str, Any]:
    economy_state = exploration_economy(
        {
            "pressure": stabilized_pressure,
            "ecology": ecology,
            "population": population,
            "memory_pressure": memory_state,
        }
    )
    resource_allocation = {
        "attention_budget": economy_state["attention_budget"],
        "mutation_budget": economy_state["mutation_budget"],
        "selection_weights": dict(economy_state["selection_weights"]),
        "runtime_slot_allocation": dict(economy_state["runtime_slot_allocation"]),
        "memory_pressure": dict(economy_state["memory_pressure"]),
    }
    return {
        "economy": economy_state,
        "resource_allocation": resource_allocation,
        "budgets": apply_economy(budgets, economy_state),
    }


__all__ = ["apply_economy", "build_economy_frame"]
