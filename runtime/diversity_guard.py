"""Stability controls for diversity-sensitive search."""

from __future__ import annotations

from typing import Mapping, Sequence


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def detect_collapse(
    diversity_history: Sequence[float],
    performance_history: Sequence[float] | None = None,
    *,
    window: int = 5,
    min_diversity: float = 0.25,
    max_drop: float = 0.35,
    stagnation_tolerance: float = 0.01,
) -> dict[str, float | bool | str]:
    """Detect whether the system is entering a diversity collapse."""
    if not diversity_history:
        return {
            "collapsed": False,
            "reason": "no_data",
            "diversity": 1.0,
            "drop": 0.0,
            "stagnating": False,
        }

    recent = list(diversity_history[-window:])
    diversity = recent[-1]
    baseline = max(recent)
    drop = 0.0 if baseline <= 0 else (baseline - diversity) / baseline

    stagnating = False
    if performance_history and len(performance_history) >= window:
        perf_recent = performance_history[-window:]
        stagnating = (max(perf_recent) - min(perf_recent)) <= stagnation_tolerance

    low_diversity = diversity <= min_diversity
    fast_drop = drop >= max_drop
    collapsed = low_diversity or (fast_drop and stagnating)

    if low_diversity:
        reason = "low_diversity"
    elif fast_drop and stagnating:
        reason = "drop_plus_stagnation"
    elif fast_drop:
        reason = "rapid_drop"
    else:
        reason = "stable"

    return {
        "collapsed": collapsed,
        "reason": reason,
        "diversity": diversity,
        "drop": drop,
        "stagnating": stagnating,
    }


def adjust_mutation_pressure(
    current_pressure: float,
    collapse_state: Mapping[str, object],
    diversity: float,
    *,
    target_diversity: float = 0.50,
    response_gain: float = 0.35,
    min_pressure: float = 0.01,
    max_pressure: float = 0.80,
) -> float:
    """Increase mutation pressure during collapse and relax it when stable."""
    collapsed = bool(collapse_state.get("collapsed", False))
    deficit = _clamp(target_diversity - diversity, 0.0, 1.0)
    delta = response_gain * deficit
    next_pressure = current_pressure + delta if collapsed else current_pressure - (delta * 0.5)
    return _clamp(next_pressure, min_pressure, max_pressure)


def adjust_exploration_ratio(
    current_ratio: float,
    collapse_state: Mapping[str, object],
    diversity: float,
    *,
    target_diversity: float = 0.50,
    response_gain: float = 0.25,
    min_ratio: float = 0.05,
    max_ratio: float = 0.95,
) -> float:
    """Shift budget toward exploration when diversity falls."""
    collapsed = bool(collapse_state.get("collapsed", False))
    deficit = _clamp(target_diversity - diversity, 0.0, 1.0)
    delta = response_gain * deficit
    next_ratio = current_ratio + delta if collapsed else current_ratio - (delta * 0.5)
    return _clamp(next_ratio, min_ratio, max_ratio)


__all__ = [
    "detect_collapse",
    "adjust_mutation_pressure",
    "adjust_exploration_ratio",
]
