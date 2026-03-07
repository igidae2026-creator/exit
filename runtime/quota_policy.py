from __future__ import annotations

from runtime.resource_allocator import allocate


def allocate_quota(pressure_vector: dict[str, float], *, base_budget: float = 100.0) -> dict[str, float]:
    allocation = allocate(pressure_vector, {}, {})
    return {
        "worker_budget": max(1.0, round(float(allocation["runtime_slots"]), 6)),
        "mutation_budget": round(float(allocation["mutation_budget"]) * base_budget, 6),
        "repair_budget": round(float(pressure_vector.get("repair_pressure", 0.0)) * base_budget, 6),
        "exploration_budget": round(float(allocation["attention_budget"]) * base_budget, 6),
        "replay_budget": round(float(allocation["memory_pressure"].get("archive_pressure", 0.0)) * base_budget, 6),
    }
