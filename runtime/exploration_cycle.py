from __future__ import annotations

from typing import Any, Mapping, Sequence


def _depth(history: Sequence[Mapping[str, Any]]) -> int:
    streak = 0
    for row in reversed(list(history)):
        quest = row.get("quest", {}) if isinstance(row.get("quest"), Mapping) else {}
        if str(quest.get("type", "")) != "exploration":
            break
        streak += 1
    return streak


def exploration_cycle(
    history: Sequence[Mapping[str, Any]],
    exploration_budget: int,
    quest: Mapping[str, Any],
) -> dict[str, Any]:
    prior_depth = _depth(history)
    next_depth = prior_depth + (1 if str((quest or {}).get("type", "")) == "exploration" else 0)
    exhausted = prior_depth >= exploration_budget or next_depth >= exploration_budget
    prior_cycles = 0
    for row in reversed(list(history)):
        cycle = row.get("exploration_cycle", {}) if isinstance(row.get("exploration_cycle"), Mapping) else {}
        if "budget_cycle_count" in cycle:
            prior_cycles = int(cycle.get("budget_cycle_count", 0) or 0)
            break
    budget_cycle_count = prior_cycles + (1 if exhausted else 0)
    return {
        "depth": next_depth,
        "limit": int(exploration_budget),
        "exhausted": exhausted,
        "exploration_budget": int(exploration_budget),
        "budget_exhausted": exhausted,
        "budget_cycle_count": budget_cycle_count,
        "new_cycle_started": exhausted,
        "next_cycle": "reframing" if exhausted else "continue",
        "archive_current_outputs": exhausted,
        "reframing_quest_required": exhausted,
    }


__all__ = ["exploration_cycle"]
