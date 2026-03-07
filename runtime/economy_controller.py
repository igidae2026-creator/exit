"""Resource allocation controls for runtime stability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from runtime.quota_policy import allocate_quota


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
    collapsed = bool(collapse_state.get("collapsed", False))
    severity = _clamp(float(collapse_state.get("drop", 0.0) or 0.0), 0.0, 1.0)
    raw = {
        "worker_budget": 0.20 + (0.10 * (1.0 - exploration_ratio)),
        "mutation_budget": 0.20 + (0.25 * mutation_pressure),
        "repair_budget": 0.08 + (0.35 * severity if collapsed else 0.06),
        "exploration_budget": 0.18 + (0.20 * exploration_ratio),
        "replay_budget": 0.08 + (0.10 * severity),
    }
    minimums = dict(minimums or {})
    total = sum(raw.values()) or 1.0
    alloc = {key: (value / total) * total_budget for key, value in raw.items()}
    for key, share in minimums.items():
        alloc[key] = max(alloc.get(key, 0.0), share * total_budget)
    scale = total_budget / (sum(alloc.values()) or total_budget)
    return {key: round(value * scale, 6) for key, value in alloc.items()}


@dataclass(slots=True)
class QuotaAllocator:
    total_budget: float = 100.0
    base_workers: int = 2

    def allocate(self, pressure_vector: Mapping[str, object], policy: Mapping[str, object] | None = None) -> dict[str, float | int]:
        quota = allocate_quota({key: float(value or 0.0) for key, value in pressure_vector.items() if isinstance(value, (int, float))}, base_budget=self.total_budget)
        policy = dict(policy or {})
        minimum_worker_budget = int(policy.get("minimum_worker_budget", 1) or 1)
        worker_hint = max(minimum_worker_budget, int(round(quota["worker_budget"] / max(1.0, self.total_budget / max(self.base_workers, 1)))))
        return {
            "mutation_budget": quota["mutation_budget"],
            "exploration_budget": quota["exploration_budget"],
            "repair_budget": quota["repair_budget"],
            "replay_budget": quota["replay_budget"],
            "worker_budget": worker_hint,
        }


__all__ = ["QuotaAllocator", "resource_allocation"]
