from __future__ import annotations

from typing import Any, Mapping

from core.quest import build_quest, choose_quest_type


def generate_quest(
    pressure_vector: Mapping[str, float],
    replay_state: object,
    *,
    domain_hint: str = "code_domain",
    tick: int,
) -> dict[str, Any]:
    quest_type = choose_quest_type(
        pressure_vector,
        plateau_streak=int(getattr(replay_state, "plateau_streak", 0) or 0),
    )

    if quest_type == "meta":
        title = "Meta stabilization quest"
        description = "Repair plateaus or instability by changing policy and recovery strategy."
    elif quest_type == "exploration":
        title = "Exploration quest"
        description = "Search for novelty and diversity in the canonical code domain."
    else:
        title = "Work quest"
        description = "Exploit the best current strategy in the canonical code domain."

    return build_quest(
        quest_type,
        domain_hint=domain_hint,
        title=title,
        description=description,
        pressures=pressure_vector,
        tick=tick,
    )
