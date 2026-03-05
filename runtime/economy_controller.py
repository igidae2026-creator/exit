"""Resource allocation controls for runtime stability."""

from __future__ import annotations

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


__all__ = ["resource_allocation"]
