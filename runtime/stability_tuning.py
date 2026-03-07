from __future__ import annotations

from typing import Any, Mapping


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, float(value))), 4)


def tune_stability(
    metrics: Mapping[str, Any],
    *,
    thresholds: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    metric_state = dict(metrics or {})
    limits = {
        "drift": float((thresholds or {}).get("drift", 0.52)),
        "stagnation": float((thresholds or {}).get("stagnation", 0.56)),
        "overexpansion": float((thresholds or {}).get("overexpansion", 0.58)),
        "underexploration": float((thresholds or {}).get("underexploration", 0.54)),
    }
    actions: list[str] = []
    if float(metric_state.get("drift_score", 0.0)) > limits["drift"]:
        actions.append("tighten_policy_mutation")
        actions.append("increase_repair_budget")
    if float(metric_state.get("stagnation_score", 0.0)) > limits["stagnation"]:
        actions.append("raise_exploration_pressure")
    if float(metric_state.get("overexpansion_score", 0.0)) > limits["overexpansion"]:
        actions.append("cap_domain_expansion")
    if float(metric_state.get("underexploration_score", 0.0)) > limits["underexploration"]:
        actions.append("rebalance_toward_exploration")
    if float(metric_state.get("concentration_streak", 0.0)) >= 6:
        actions.extend(
            [
                "force_branching_pressure",
                "force_evaluation_diversification",
                "reduce_dominant_lineage_allocation",
            ]
        )
    return {
        "thresholds": {key: _clamp(value) for key, value in limits.items()},
        "stability_actions": actions[:6],
        "bounded": True,
    }


__all__ = ["tune_stability"]
