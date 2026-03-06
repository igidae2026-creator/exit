from __future__ import annotations

from typing import Any, Mapping

from metaos.runtime.meta_cooldown import quest_cooldown


QUEST_TYPES = {"work", "exploration", "meta", "reframing", "repair"}


def _count(recent_state: Mapping[str, Any], key: str) -> int:
    return int(recent_state.get(key, 0) or 0)


def meta_quest(
    pressure: Mapping[str, float],
    recent_state: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    recent_state = dict(recent_state or {})
    cooldown_state = quest_cooldown(recent_state)
    reasons: list[str] = []
    novelty_low = _count(recent_state, "novelty_low_streak") >= 3 or float(pressure.get("novelty_pressure", 0.0)) >= 0.9
    lineage_trigger = _count(recent_state, "lineage_high_streak") >= 3 or float(pressure.get("lineage_pressure", 0.0)) >= 0.75
    routing_trigger = _count(recent_state, "routing_stagnation") >= 4 or float(pressure.get("domain_shift_pressure", 0.0)) >= 0.85
    reframing_failure = _count(recent_state, "failed_reframing_repeat") >= 2 or float(pressure.get("reframing_pressure", 0.0)) >= 0.8

    if _count(recent_state, "plateau_streak") >= 3:
        reasons.append("plateau_sustained")
    if novelty_low:
        reasons.append("novelty_sustained_low")
    if lineage_trigger:
        reasons.append("lineage_concentration_sustained_high")
    if _count(recent_state, "repair_cycle_streak") >= 3 or float(pressure.get("repair_pressure", 0.0)) >= 0.85:
        reasons.append("repeated_repair_cycles")
    if routing_trigger:
        reasons.append("domain_routing_stagnates")
    if reframing_failure:
        reasons.append("reframing_attempts_failed")

    if cooldown_state["meta_locked"]:
        return None
    if not novelty_low:
        return None
    if not (lineage_trigger or routing_trigger or reframing_failure):
        return None
    if recent_state.get("guard_active") and cooldown_state["preferred_type"] == "exploration":
        return None

    return {
        "type": "meta",
        "priority": "high",
        "reasons": reasons,
        "quest_types": sorted(QUEST_TYPES),
        "pressure": {key: round(float(value), 4) for key, value in dict(pressure).items()},
        "cooldown": cooldown_state,
    }
