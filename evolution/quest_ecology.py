from __future__ import annotations

from typing import Any

from metaos.runtime.knowledge_system import accumulated_knowledge


DEPRECATED_MODULE = "evolution.quest_ecology"
CANONICAL_MODULE = "metaos.runtime.knowledge_system"


def choose_quest_kind(replay_state: Any, pressure_vector: dict[str, float], *, data_dir: str = "data") -> str:
    if float(pressure_vector.get("reframing_pressure", 0.0)) >= 0.6:
        return "reframing_quest"
    if float(pressure_vector.get("repair_pressure", 0.0)) >= 0.7:
        return "meta_quest"
    if float(pressure_vector.get("novelty_pressure", 0.0)) >= 0.5 or float(pressure_vector.get("diversity_pressure", 0.0)) >= 0.5:
        return "exploration_quest"
    return "work_quest"


def quest_payload(kind: str, pressure_vector: dict[str, float], *, domain: str = "code_domain") -> dict[str, Any]:
    return {
        "quest_type": kind,
        "title": kind.replace("_", " ").title(),
        "description": "Generated from deprecated evolution quest shim.",
        "domain": domain,
        "pressure_snapshot": dict(pressure_vector),
        "knowledge": accumulated_knowledge()["references"],
    }


def generate_quest_portfolio(replay_state: Any, pressure_vector: dict[str, float], *, max_quests: int = 3) -> list[dict[str, Any]]:
    primary = choose_quest_kind(replay_state, pressure_vector)
    out = [quest_payload(primary, pressure_vector)]
    if primary != "exploration_quest" and len(out) < max_quests:
        out.append(quest_payload("exploration_quest", pressure_vector))
    return out[:max_quests]
