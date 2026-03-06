"""Resource allocation controls for runtime stability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def resource_allocation(
    total_budget: float,
    collapse_state: Mapping[str, object],
    exploration_ratio: float,
    mutation_pressure: float,
    *,
    minimums: Mapping[str, float] | None = None,
) -> dict[str, float]:
    """
    Allocate budget across exploit/explore/recovery/mutation buckets.

    The output always sums to ``total_budget`` (within floating-point tolerance).
    """
    if total_budget <= 0:
        return {"exploit": 0.0, "explore": 0.0, "recovery": 0.0, "mutation": 0.0}

    minimums = dict(minimums or {})
    collapsed = bool(collapse_state.get("collapsed", False))
    severity = float(collapse_state.get("drop", 0.0) or 0.0)
    severity = _clamp(severity, 0.0, 1.0)

    explore_weight = _clamp(exploration_ratio, 0.0, 1.0)
    mutation_weight = _clamp(mutation_pressure, 0.0, 1.0)

    recovery_boost = 0.10 + (0.30 * severity) if collapsed else 0.02
    exploit_weight = max(0.0, 1.0 - explore_weight)

    raw = {
        "exploit": exploit_weight,
        "explore": explore_weight,
        "recovery": recovery_boost,
        "mutation": mutation_weight,
    }

    weight_sum = sum(raw.values()) or 1.0
    alloc = {k: (v / weight_sum) * total_budget for k, v in raw.items()}

    # Honor minimum shares, then rescale any remaining budget proportionally.
    enforced = {k: max(alloc[k], minimums.get(k, 0.0) * total_budget) for k in alloc}
    used = sum(enforced.values())
    if used > total_budget:
        scale = total_budget / used
        return {k: v * scale for k, v in enforced.items()}

    remaining = total_budget - used
    if remaining == 0:
        return enforced

    flex_weights = {k: raw[k] for k in raw}
    flex_sum = sum(flex_weights.values()) or 1.0
    for key in enforced:
        enforced[key] += remaining * (flex_weights[key] / flex_sum)

    return enforced


@dataclass(slots=True)
class QuotaAllocator:
    total_budget: float = 1.0
    base_workers: int = 2

    def allocate(
        self,
        pressure_vector: Mapping[str, object],
        policy: Mapping[str, object] | None = None,
    ) -> dict[str, float | int]:
        policy = dict(policy or {})
        exploration_pressure = _clamp(float(pressure_vector.get("exploration", 0.2) or 0.0), 0.0, 1.0)
        repair_pressure = _clamp(float(pressure_vector.get("repair", 0.1) or 0.0), 0.0, 1.0)
        diversity_pressure = _clamp(float(pressure_vector.get("diversity", 0.1) or 0.0), 0.0, 1.0)
        replay_pressure = _clamp(float(pressure_vector.get("replay", 0.1) or 0.0), 0.0, 1.0)
        collapse_pressure = _clamp(float(pressure_vector.get("collapse", 0.0) or 0.0), 0.0, 1.0)

        raw = {
            "mutation_budget": max(0.05, 0.25 + (exploration_pressure * 0.35) + (diversity_pressure * 0.15)),
            "exploration_budget": max(0.05, 0.20 + (exploration_pressure * 0.40) + (diversity_pressure * 0.20)),
            "repair_budget": max(0.05, 0.10 + (repair_pressure * 0.55) + (collapse_pressure * 0.15)),
            "replay_budget": max(0.05, 0.10 + (replay_pressure * 0.50) + (repair_pressure * 0.10)),
            "worker_budget": max(0.05, 0.20 + (collapse_pressure * 0.20) + (exploration_pressure * 0.10)),
        }

        total = sum(raw.values()) or 1.0
        budgets = {name: (value / total) * self.total_budget for name, value in raw.items()}

        minimum_worker_budget = int(policy.get("minimum_worker_budget", 1) or 1)
        base_worker_budget = int(policy.get("base_worker_budget", self.base_workers) or self.base_workers)
        dynamic_workers = base_worker_budget + int(round(collapse_pressure * 2)) + int(round(exploration_pressure))

        return {
            "mutation_budget": round(budgets["mutation_budget"], 6),
            "exploration_budget": round(budgets["exploration_budget"], 6),
            "repair_budget": round(budgets["repair_budget"], 6),
            "replay_budget": round(budgets["replay_budget"], 6),
            "worker_budget": max(minimum_worker_budget, dynamic_workers),
        }


__all__ = ["QuotaAllocator", "resource_allocation"]
