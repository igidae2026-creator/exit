from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from runtime.hysteresis import bounded_step
from runtime.profiles import runtime_profile


def _clamp(value: float, low: float, high: float) -> float:
    if not math.isfinite(value):
        return low
    return max(low, min(high, value))


def _previous_workers(history: Sequence[Mapping[str, Any]] | None) -> int | None:
    for row in reversed(list(history or [])):
        if "workers" in row:
            return max(1, int(row.get("workers", 1)))
        budgets = row.get("budgets", {}) if isinstance(row.get("budgets"), Mapping) else {}
        if "effective_workers" in budgets:
            return max(1, int(budgets.get("effective_workers", 1)))
    return None


def allocate(
    pressure: Mapping[str, float],
    workers: int,
    market_state: Mapping[str, float] | None = None,
    *,
    guard: Mapping[str, Any] | None = None,
    history: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, float | int]:
    guard = dict(guard or {})
    profile = runtime_profile(str(guard.get("runtime_profile") or ""))
    floor = max(2 if guard.get("downshift_workers") else profile.worker_min, 1)
    ceiling = max(profile.worker_max, floor)
    base = max(floor, int(workers))
    novelty = float(pressure.get("novelty_pressure", 0.0))
    diversity = float(pressure.get("diversity_pressure", 0.0))
    domain_shift = float(pressure.get("domain_shift_pressure", 0.0))
    up = novelty + diversity + domain_shift
    down = float(pressure.get("repair_pressure", 0)) + float(pressure.get("efficiency_pressure", 0))
    scale = 1.0 + (0.35 * up) - (0.25 * down)
    scale = max(0.5, min(2.0, scale))
    target_workers = max(floor, int(base * scale))
    prev_workers = _previous_workers(history)
    strong_combined_pressure = (
        novelty >= 0.95 and diversity >= 0.65 and domain_shift >= 0.45
    ) or up >= 2.2
    exploratory_not_critical = up >= 1.0 and not strong_combined_pressure and down <= 1.0
    if not guard.get("downshift_workers") and exploratory_not_critical:
        target_workers = int(_clamp(float(target_workers), float(profile.worker_min), float(ceiling)))
        if prev_workers is not None and prev_workers >= ceiling:
            target_workers = min(target_workers, ceiling - max(1, int((ceiling - profile.worker_min) * 0.1)))
    elif not guard.get("downshift_workers") and not strong_combined_pressure and down < 0.9:
        target_workers = int(_clamp(float(target_workers), float(profile.worker_min), float(ceiling)))
    if prev_workers is not None:
        max_delta = 1.0 if guard.get("downshift_workers") else (2.0 if float(pressure.get("repair_pressure", 0.0)) <= 0.35 else 1.0)
        hi = max(float(target_workers), float(prev_workers), float(floor))
        if not strong_combined_pressure and not guard.get("downshift_workers"):
            hi = min(float(ceiling), hi)
        effective_workers = int(
            round(
                bounded_step(
                    float(prev_workers),
                    float(target_workers),
                    max_delta=max_delta,
                    lo=float(floor),
                    hi=hi,
                )
            )
        )
    else:
        effective_workers = target_workers
    if not strong_combined_pressure and not guard.get("downshift_workers"):
        effective_workers = int(_clamp(float(effective_workers), float(profile.worker_min), float(ceiling)))
    market_state = dict(market_state or {})
    mutation_bias = float(market_state.get("mutation_bias", 0.2))
    archive_bias = float(market_state.get("archive_bias", 0.2))
    repair_bias = float(market_state.get("repair_bias", 0.2))
    domain_bias = float(market_state.get("domain_budget_bias", 0.2))
    replay_bias = float(market_state.get("selection_bias", 0.2))
    total_budget = float(effective_workers * 10)
    budgets = {
        "worker_budget": effective_workers,
        "mutation_budget": round(_clamp(total_budget * (0.20 + mutation_bias), 8.0, 80.0), 4),
        "replay_budget": round(_clamp(total_budget * (0.15 + replay_bias), 4.0, 80.0), 4),
        "repair_budget": round(_clamp(total_budget * (0.10 + repair_bias), 0.0, 60.0), 4),
        "archive_budget": round(_clamp(total_budget * (0.10 + archive_bias), 4.0, 60.0), 4),
        "domain_budget": round(_clamp(total_budget * (0.10 + domain_bias), 4.0, 60.0), 4),
        "workers": effective_workers,
        "effective_workers": effective_workers,
    }
    return budgets
