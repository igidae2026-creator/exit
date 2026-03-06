from __future__ import annotations


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def allocate_quota(pressure_vector: dict[str, float], *, base_budget: float = 100.0) -> dict[str, float]:
    novelty = _clamp01(float(pressure_vector.get("novelty_pressure", 0.0)))
    diversity = _clamp01(float(pressure_vector.get("diversity_pressure", 0.0)))
    efficiency = _clamp01(float(pressure_vector.get("efficiency_pressure", 0.0)))
    repair = _clamp01(float(pressure_vector.get("repair_pressure", 0.0)))
    reframing = _clamp01(float(pressure_vector.get("reframing_pressure", 0.0)))
    transfer = _clamp01(float(pressure_vector.get("transfer_pressure", 0.0)))
    archive = _clamp01(float(pressure_vector.get("archive_pressure", 0.0)))

    weights = {
        "worker_budget": 0.20 + (0.15 * efficiency) + (0.10 * transfer),
        "mutation_budget": 0.16 + (0.24 * novelty) + (0.10 * diversity),
        "repair_budget": 0.08 + (0.34 * repair),
        "exploration_budget": 0.18 + (0.16 * max(novelty, diversity, reframing, transfer)),
        "replay_budget": 0.08 + (0.16 * max(archive, repair, reframing)),
    }
    total = sum(weights.values()) or 1.0
    budgets = {key: round((value / total) * base_budget, 6) for key, value in weights.items()}
    budgets["worker_budget"] = max(1.0, round(budgets["worker_budget"], 6))
    return budgets
