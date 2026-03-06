from __future__ import annotations


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def allocate_quota(pressure_vector: dict[str, float], *, base_budget: float = 100.0) -> dict[str, float]:
    novelty = _clamp01(float(pressure_vector.get("novelty_pressure", 0.0)))
    diversity = _clamp01(float(pressure_vector.get("diversity_pressure", 0.0)))
    efficiency = _clamp01(float(pressure_vector.get("efficiency_pressure", 0.0)))
    repair = _clamp01(float(pressure_vector.get("repair_pressure", 0.0)))
    reframing = _clamp01(float(pressure_vector.get("reframing_pressure", 0.0)))

    weights = {
        "worker_budget": 0.25 + (0.15 * efficiency),
        "mutation_budget": 0.15 + (0.20 * novelty),
        "repair_budget": 0.10 + (0.30 * repair),
        "exploration_budget": 0.20 + (0.20 * max(novelty, diversity, reframing)),
        "replay_budget": 0.10 + (0.10 * diversity),
    }
    total_weight = sum(weights.values()) or 1.0
    return {key: round((value / total_weight) * base_budget, 6) for key, value in weights.items()}
