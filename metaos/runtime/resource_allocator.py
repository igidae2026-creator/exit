from __future__ import annotations

from typing import Any, Mapping

from metaos.runtime.exploration_economy import allocate_resources


def allocate(
    pressure: Mapping[str, float],
    ecology: Mapping[str, Any],
    population: Mapping[str, Any],
    memory_state: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    allocation = allocate_resources(pressure, ecology, population, memory_state=memory_state)
    runtime_slot_allocation = dict(allocation.get("runtime_slot_allocation", {}))
    return {
        "attention_budget": allocation["attention_budget"],
        "mutation_budget": allocation["mutation_budget"],
        "selection_weights": dict(allocation["selection_weights"]),
        "runtime_slots": int(runtime_slot_allocation.get("runtime_slots", 0)),
        "runtime_slot_allocation": runtime_slot_allocation,
        "memory_pressure": dict(allocation["memory_pressure"]),
    }


__all__ = ["allocate"]
