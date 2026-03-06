from __future__ import annotations

from typing import Any

from artifact.lineage import lineage_concentration


def choose_quest_kind(replay_state: object, pressure_vector: dict[str, float], *, data_dir: str = "data") -> str:
    plateau = int(getattr(replay_state, "plateau_streak", 0) or 0)
    repair = float(pressure_vector.get("repair_pressure", 0.0))
    novelty = float(pressure_vector.get("novelty_pressure", 0.0))
    diversity = float(pressure_vector.get("diversity_pressure", 0.0))
    reframing = float(pressure_vector.get("reframing_pressure", 0.0))
    concentration = lineage_concentration(data_dir)

    if reframing >= 0.7 or concentration >= 0.45:
        return "reframing_quest"
    if repair >= 0.75:
        return "meta_quest"
    if plateau >= 2 or novelty >= 0.55 or diversity >= 0.55:
        return "exploration_quest"
    return "work_quest"


def quest_payload(kind: str, pressure_vector: dict[str, float]) -> dict[str, Any]:
    titles = {
        "work_quest": "Work quest",
        "exploration_quest": "Exploration quest",
        "meta_quest": "Meta quest",
        "reframing_quest": "Reframing quest",
    }
    descriptions = {
        "work_quest": "Exploit the current frontier in the canonical domain.",
        "exploration_quest": "Search for new novelty and diversity.",
        "meta_quest": "Repair system behavior and update policies.",
        "reframing_quest": "Reframe the search objective to escape concentration.",
    }
    return {
        "quest_type": kind,
        "title": titles[kind],
        "description": descriptions[kind],
        "pressure_snapshot": dict(pressure_vector),
    }
