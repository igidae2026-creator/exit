from __future__ import annotations

from typing import Any, Mapping

from metaos.runtime.memory_pressure import memory_pressure


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, float(value))), 4)


def allocate_resources(
    pressure: Mapping[str, float],
    ecology: Mapping[str, Any],
    population: Mapping[str, Any],
    memory_state: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    pressure_state = dict(pressure or {})
    ecology_state = dict(ecology or {})
    population_state = dict(population or {})
    population_counts = dict(population_state.get("population_counts", {})) if isinstance(population_state.get("population_counts"), Mapping) else {}
    growth_rates = dict(population_state.get("growth_rates", {})) if isinstance(population_state.get("growth_rates"), Mapping) else {}
    extinction_risk = dict(population_state.get("extinction_risk", {})) if isinstance(population_state.get("extinction_risk"), Mapping) else {}
    memory_state = dict(memory_state or memory_pressure())

    novelty = float(pressure_state.get("novelty_pressure", 0.0))
    diversity = float(pressure_state.get("diversity_pressure", 0.0))
    efficiency = float(pressure_state.get("efficiency_pressure", 0.0))
    repair = float(pressure_state.get("repair_pressure", 0.0))
    domain_shift = float(pressure_state.get("domain_shift_pressure", 0.0))
    reframing = float(pressure_state.get("reframing_pressure", 0.0))
    exploration_gap = 1.0 - float(ecology_state.get("exploration_health", 0.5))
    diversity_gap = 1.0 - float(ecology_state.get("diversity_health", 0.5))

    attention_budget = _clamp(0.32 + 0.20 * novelty + 0.10 * reframing + 0.08 * exploration_gap)
    mutation_budget = _clamp(0.26 + 0.15 * novelty + 0.12 * domain_shift + 0.08 * diversity_gap - 0.06 * repair)
    selection_weights = {
        "strategy": _clamp(0.18 + 0.10 * novelty),
        "policy": _clamp(0.16 + 0.10 * float(population_counts.get("policy", 0) == 0) + 0.05 * memory_state["knowledge_density"]),
        "quest": _clamp(0.14 + 0.10 * reframing + 0.12 * repair),
        "evaluation": _clamp(0.16 + 0.10 * float(extinction_risk.get("evaluation", 0.0)) + 0.04 * diversity_gap),
        "allocator": _clamp(0.12 + 0.10 * efficiency + 0.06 * memory_state["archive_pressure"]),
        "domain_genome": _clamp(0.16 + 0.12 * domain_shift + 0.08 * max(0.0, -float(growth_rates.get("domain", 0.0)))),
    }
    total = sum(selection_weights.values()) or 1.0
    selection_weights = {key: round(value / total, 4) for key, value in selection_weights.items()}
    runtime_slot_allocation = {
        "runtime_slots": max(3, int(round(4 + (8 * attention_budget)))),
        "exploration_slots": max(1, int(round(1 + (5 * mutation_budget)))),
        "memory_slots": max(1, int(round(1 + (4 * memory_state["knowledge_density"])))),
        "repair_slots": max(1, int(round(1 + (4 * repair)))),
    }
    return {
        "attention_budget": attention_budget,
        "mutation_budget": mutation_budget,
        "selection_weights": selection_weights,
        "runtime_slot_allocation": runtime_slot_allocation,
        "memory_pressure": memory_state,
    }


def exploration_economy(state: Mapping[str, Any]) -> dict[str, Any]:
    return allocate_resources(
        dict(state.get("pressure", {})) if isinstance(state.get("pressure"), Mapping) else {},
        dict(state.get("ecology", {})) if isinstance(state.get("ecology"), Mapping) else {},
        dict(state.get("population", {})) if isinstance(state.get("population"), Mapping) else {},
        dict(state.get("memory_pressure", {})) if isinstance(state.get("memory_pressure"), Mapping) else None,
    )
