from __future__ import annotations

from typing import Any, Mapping

from runtime.hysteresis import cooldown


def quest_cooldown(recent_state: Mapping[str, Any]) -> dict[str, Any]:
    recent_state = dict(recent_state or {})
    meta_repeat = int(recent_state.get("meta_repeat", 0))
    reframing_repeat = int(recent_state.get("reframing_repeat", 0))
    repair_repeat = int(recent_state.get("repair_repeat", 0))
    guard_active = bool(recent_state.get("guard_active", False))
    meta_share = float(recent_state.get("meta_share", 0.0) or 0.0)

    meta_locked = cooldown(meta_repeat, 2) or meta_share > 0.45
    reframing_locked = cooldown(reframing_repeat, 2)
    repair_locked = cooldown(repair_repeat, 3)

    preferred = "exploration" if (guard_active or meta_locked or reframing_locked) else "work"
    if meta_share > 0.45:
        preferred = "exploration" if guard_active or meta_share > 0.60 else "work"
    if meta_share > 0.60:
        preferred = "exploration"
    if repair_locked:
        preferred = "work"

    return {
        "meta_repeat": meta_repeat,
        "reframing_repeat": reframing_repeat,
        "repair_repeat": repair_repeat,
        "meta_share": round(meta_share, 4),
        "meta_locked": meta_locked,
        "reframing_locked": reframing_locked,
        "repair_locked": repair_locked,
        "preferred_type": preferred,
        "force_exploration": meta_share > 0.60,
        "cross_domain_bias": meta_share > 0.45,
        "reframing_bias": meta_share > 0.45 and not reframing_locked,
    }
