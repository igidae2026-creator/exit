from __future__ import annotations

from typing import Any, Mapping

from kernel.contracts import QuestSlots
from metaos.runtime.meta_quest_engine import meta_quest
from metaos.runtime.quest_system import spawn_quest as legacy_spawn_quest


def quest_slots(
    pressure: Mapping[str, float],
    *,
    recent_state: Mapping[str, Any] | None = None,
    plateau_hit: bool = False,
    lineage_high: bool = False,
    novelty_low_sustained: bool = False,
) -> QuestSlots:
    continuity = legacy_spawn_quest(
        pressure,
        plateau_hit=plateau_hit,
        lineage_high=lineage_high,
        novelty_low_sustained=novelty_low_sustained,
    )
    frontier = {"type": "exploration", "priority": "high"}
    escape = meta_quest(pressure, recent_state=recent_state or {}) or {"type": "repair", "priority": "high"}
    return QuestSlots(continuity_slot=continuity, frontier_slot=frontier, escape_slot=escape)


def active_quest(slots: QuestSlots, preferred: str | None = None) -> dict[str, Any]:
    if preferred == "escape":
        return dict(slots.escape_slot)
    if preferred == "frontier":
        return dict(slots.frontier_slot)
    return dict(slots.continuity_slot)

