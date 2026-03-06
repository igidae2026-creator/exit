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
    return {
        "depth": next_depth,
        "limit": int(exploration_budget),
        "exhausted": exhausted,
        "next_cycle": "reframing" if exhausted else "continue",
        "archive_current_outputs": exhausted,
    }


__all__ = ["exploration_cycle"]
