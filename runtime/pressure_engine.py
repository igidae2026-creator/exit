from __future__ import annotations

from typing import Any, Mapping

from runtime.pressure_model import CANONICAL_PRESSURES, compute_pressure


def compute_pressures(replay_state: Any) -> dict[str, float]:
    latest = getattr(replay_state, "latest_metrics", {}) or {}
    history = getattr(replay_state, "metric_history", []) or []
    out = compute_pressure(latest, history=history)
    pressure = dict(out["pressure"])
    return {key: float(pressure.get(key, 0.0)) for key in CANONICAL_PRESSURES}
