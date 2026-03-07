from __future__ import annotations

from typing import Any, Mapping

from runtime.hysteresis import bounded_step, clamp01, smooth


def stabilize_market(
    current: Mapping[str, float],
    previous: Mapping[str, Any] | None = None,
    guard: Mapping[str, Any] | None = None,
) -> dict[str, float]:
    previous = dict(previous or {})
    guard = dict(guard or {})
    stabilized: dict[str, float] = {}
    for key, value in dict(current).items():
        prev_value = previous.get(key)
        smoothed = smooth(float(value), prev=float(prev_value) if prev_value is not None else None, alpha=0.2)
        bounded = bounded_step(float(prev_value if prev_value is not None else value), smoothed, max_delta=0.06) if prev_value is not None else float(value)
        stabilized[key] = round(max(0.08, min(0.55, clamp01(bounded))), 6)
    if guard.get("reset_mutation_bias"):
        stabilized["mutation_bias"] = round(max(0.16, min(0.24, stabilized.get("mutation_bias", 0.2))), 6)
    if guard.get("repair_storm"):
        stabilized["repair_bias"] = round(max(stabilized.get("repair_bias", 0.2), 0.22), 6)
        stabilized["selection_bias"] = round(min(stabilized.get("selection_bias", 0.2), 0.32), 6)
    total = sum(stabilized.values()) or 1.0
    normalized = {key: round(value / total, 6) for key, value in stabilized.items()}
    correction = round(1.0 - sum(normalized.values()), 6)
    last_key = next(reversed(normalized))
    normalized[last_key] = round(max(0.0, normalized[last_key] + correction), 6)
    return normalized
