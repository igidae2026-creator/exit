from __future__ import annotations

from typing import Any, Mapping, Sequence

from runtime.hysteresis import bounded_step, clamp01, smooth


def _last_pressure(history: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    for row in reversed(list(history)):
        if isinstance(row.get("stabilized_pressure"), Mapping):
            return {key: float(value) for key, value in row["stabilized_pressure"].items()}
        if isinstance(row.get("pressure"), Mapping):
            return {key: float(value) for key, value in row["pressure"].items()}
    return {}


def _guard_active_ticks(history: Sequence[Mapping[str, Any]], key: str) -> int:
    count = 0
    for row in reversed(list(history)[-8:]):
        guard = row.get("guard", {}) if isinstance(row.get("guard"), Mapping) else {}
        if bool(guard.get(key)):
            count += 1
        else:
            break
    return count


def stabilize_pressure(
    current: Mapping[str, float],
    history: Sequence[Mapping[str, Any]] | None = None,
    guard: Mapping[str, Any] | None = None,
) -> dict[str, float]:
    history = list(history or [])
    guard = dict(guard or {})
    prev = _last_pressure(history)
    stabilized: dict[str, float] = {}

    for key, value in dict(current).items():
        current_value = clamp01(float(value))
        prev_value = prev.get(key)
        smoothed = smooth(current_value, prev=prev_value, alpha=0.22)
        limit = 0.06 if key in {"reframing_pressure", "domain_shift_pressure"} else 0.08
        if prev_value is None:
            bounded = current_value
        else:
            bounded = bounded_step(prev_value, smoothed, max_delta=limit)
        stabilized[key] = round(clamp01(bounded), 4)

    if guard.get("freeze_export") and _guard_active_ticks(history, "freeze_export") >= 2:
        stabilized["repair_pressure"] = round(max(0.0, stabilized.get("repair_pressure", 0.0) - 0.08), 4)
    if guard.get("downshift_workers") and _guard_active_ticks(history, "downshift_workers") >= 2:
        stabilized["repair_pressure"] = round(max(0.0, stabilized.get("repair_pressure", 0.0) - 0.06), 4)
    if guard.get("force_meta"):
        stabilized["reframing_pressure"] = round(max(0.0, stabilized.get("reframing_pressure", 0.0) - 0.05), 4)
        stabilized["domain_shift_pressure"] = round(max(0.0, stabilized.get("domain_shift_pressure", 0.0) - 0.04), 4)
    if guard.get("force_reframing"):
        stabilized["reframing_pressure"] = round(min(0.72, stabilized.get("reframing_pressure", 0.0)), 4)

    return stabilized
