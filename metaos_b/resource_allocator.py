from __future__ import annotations

from typing import Any, Mapping

from runtime.resource_allocator import allocate


def allocate_for_units(
    pressure: Mapping[str, float],
    ecology: Mapping[str, Any],
    population: Mapping[str, Any],
    domain_names: list[str],
) -> dict[str, Any]:
    shared = allocate(pressure, ecology, population)
    per_unit_budget = round(float(shared["exploration_budget"]) / max(1, len(domain_names)), 4)
    per_unit_slots = max(1, int(shared["runtime_slots"]) // max(1, len(domain_names)))
    return {
        "shared": shared,
        "per_unit_budget": {name: per_unit_budget for name in domain_names},
        "per_unit_slots": {name: per_unit_slots for name in domain_names},
    }


__all__ = ["allocate_for_units"]
