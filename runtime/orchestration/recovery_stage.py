from __future__ import annotations

from typing import Any, Mapping


def soften_worker_budget(
    budgets: Mapping[str, float | int],
    pressure: Mapping[str, float],
    guard: Mapping[str, Any],
    quest: Mapping[str, Any],
    repair: Any,
) -> dict[str, float | int]:
    out = dict(budgets)
    effective_workers = int(out.get("effective_workers", out.get("workers", 0)))
    if effective_workers < 28:
        return out
    if repair or bool(guard.get("freeze_export")) or bool(guard.get("downshift_workers")):
        return out
    if str((quest or {}).get("type", "")) == "meta":
        return out
    combined_pressure = float(pressure.get("novelty_pressure", 0.0)) + float(pressure.get("diversity_pressure", 0.0)) + float(pressure.get("domain_shift_pressure", 0.0))
    if combined_pressure >= 2.15:
        return out
    reduced_workers = max(12, int(round(effective_workers * 0.93)))
    if reduced_workers >= effective_workers:
        reduced_workers = effective_workers - 1
    if reduced_workers < 12:
        return out
    scale = reduced_workers / max(1, effective_workers)
    for key in ("mutation_budget", "replay_budget", "repair_budget", "archive_budget", "domain_budget"):
        out[key] = round(float(out.get(key, 0.0)) * scale, 4)
    out["worker_budget"] = reduced_workers
    out["workers"] = reduced_workers
    out["effective_workers"] = reduced_workers
    return out


def validate_step_state(payload: Mapping[str, Any]) -> None:
    required = ("quest", "policy", "pressure", "stabilized_pressure", "routing", "workers", "resource_allocation", "exploration_economy_state")
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"invalid runtime state missing: {', '.join(missing)}")
    if int(payload.get("workers", 0) or 0) <= 0:
        raise ValueError("invalid runtime state workers <= 0")


__all__ = ["soften_worker_budget", "validate_step_state"]
