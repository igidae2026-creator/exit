from __future__ import annotations

from collections.abc import Mapping

from runtime.diversity_guard import detect_collapse


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def compute_pressures(replay_state: object) -> dict[str, float]:
    latest = getattr(replay_state, "latest_metrics", {}) or {}
    metric_history = getattr(replay_state, "metric_history", []) or []
    plateau_streak = int(getattr(replay_state, "plateau_streak", 0) or 0)
    supervisor_mode = str(getattr(replay_state, "supervisor_mode", "normal") or "normal")
    retry_count = int(getattr(replay_state, "retry_count", 0) or 0)

    diversity_history = [float(row.get("diversity", 0.5)) for row in metric_history if isinstance(row, Mapping)]
    score_history = [float(row.get("score", 0.5)) for row in metric_history if isinstance(row, Mapping)]
    collapse = detect_collapse(diversity_history, score_history)

    novelty_pressure = _clamp01(1.0 - float(latest.get("novelty", 0.5)))
    diversity_pressure = _clamp01(max(1.0 - float(latest.get("diversity", 0.5)), float(collapse.get("drop", 0.0) or 0.0)))
    efficiency_pressure = _clamp01(1.0 - float(latest.get("efficiency", 0.5)))

    repair_pressure = 0.0
    if bool(collapse.get("collapsed", False)):
        repair_pressure = max(repair_pressure, 0.65)
    if plateau_streak >= 2:
        repair_pressure = max(repair_pressure, 0.55)
    if retry_count > 0 or supervisor_mode == "safe_mode":
        repair_pressure = max(repair_pressure, 0.85)

    domain_shift_pressure = 0.2
    if plateau_streak >= 2:
        domain_shift_pressure = 0.7
    if novelty_pressure >= 0.6 and diversity_pressure >= 0.6:
        domain_shift_pressure = max(domain_shift_pressure, 0.8)

    return {
        "novelty_pressure": round(novelty_pressure, 6),
        "diversity_pressure": round(diversity_pressure, 6),
        "efficiency_pressure": round(efficiency_pressure, 6),
        "repair_pressure": round(_clamp01(repair_pressure), 6),
        "domain_shift_pressure": round(_clamp01(domain_shift_pressure), 6),
    }
