from __future__ import annotations

from typing import Any, Mapping


VALID_MODES = {"perpetual", "bounded"}


def validate_runtime_gates(payload: Mapping[str, Any]) -> dict[str, Any]:
    mode = str(payload.get("mode", "bounded"))
    tick_boundary_only = bool(payload.get("tick_boundary_only", True))
    max_ticks = payload.get("max_ticks")
    allow_stop = bool(payload.get("allow_stop", mode == "bounded"))

    reasons: list[str] = []
    if mode not in VALID_MODES:
        reasons.append("invalid_mode")
    if not tick_boundary_only:
        reasons.append("tick_boundary_violation")

    if mode == "perpetual":
        if max_ticks not in (None, 0):
            reasons.append("perpetual_mode_must_not_define_max_ticks")
        if allow_stop:
            reasons.append("perpetual_mode_must_not_allow_stop")
    elif mode == "bounded":
        if not isinstance(max_ticks, int) or max_ticks <= 0:
            reasons.append("bounded_mode_requires_positive_max_ticks")

    return {
        "name": "gates",
        "ok": not reasons,
        "mode": mode,
        "tick_boundary_only": tick_boundary_only,
        "max_ticks": max_ticks,
        "allow_stop": allow_stop,
        "reasons": reasons,
    }
