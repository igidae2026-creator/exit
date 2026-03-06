from __future__ import annotations

import json
import os
import random
import uuid
from datetime import datetime, timezone
from typing import Any, Mapping

QUEST_PATH = "state/quest.json"
QUEST_TYPES = ("work", "exploration", "meta")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_quest() -> dict[str, Any] | None:
    if not os.path.exists(QUEST_PATH):
        return None
    try:
        with open(QUEST_PATH, "r", encoding="utf-8") as handle:
            row = json.load(handle)
    except Exception:
        return None
    return row if isinstance(row, dict) else None


def save_quest(quest: Mapping[str, Any]) -> None:
    os.makedirs("state", exist_ok=True)
    tmp = f"{QUEST_PATH}.tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(dict(quest), handle, ensure_ascii=False, indent=2)
    os.replace(tmp, QUEST_PATH)


def build_quest(
    quest_type: str,
    *,
    domain_hint: str | None = None,
    title: str | None = None,
    description: str | None = None,
    pressures: Mapping[str, float] | None = None,
    tick: int = 0,
    ttl_ticks: int | None = None,
) -> dict[str, Any]:
    if quest_type not in QUEST_TYPES:
        raise ValueError(f"unsupported quest type: {quest_type}")

    return {
        "id": str(uuid.uuid4()),
        "quest_type": quest_type,
        "title": title or f"{quest_type.title()} quest",
        "description": description or f"Advance the {quest_type} frontier.",
        "created_at": now(),
        "domain_hint": domain_hint,
        "target": {
            "min_score": round(random.uniform(0.50, 0.75), 3),
            "min_novelty": round(random.uniform(0.35, 0.75), 3),
            "min_diversity": round(random.uniform(0.35, 0.75), 3),
        },
        "ttl_ticks": ttl_ticks if ttl_ticks is not None else random.randint(3, 8),
        "tick_start": tick,
        "wins": 0,
        "fails": 0,
        "pressure_snapshot": dict(pressures or {}),
    }


def default_quest(domain_hint: str | None = None, quest_type: str = "work") -> dict[str, Any]:
    return build_quest(quest_type, domain_hint=domain_hint)


def choose_quest_type(
    pressure_vector: Mapping[str, float] | None,
    *,
    plateau_streak: int = 0,
) -> str:
    pressure_vector = dict(pressure_vector or {})
    repair_pressure = float(pressure_vector.get("repair_pressure", 0.0))
    novelty_pressure = float(pressure_vector.get("novelty_pressure", 0.0))
    diversity_pressure = float(pressure_vector.get("diversity_pressure", 0.0))
    domain_shift_pressure = float(pressure_vector.get("domain_shift_pressure", 0.0))

    if repair_pressure >= 0.75:
        return "meta"
    if plateau_streak >= 2:
        return "meta" if repair_pressure >= 0.55 else "exploration"
    if max(novelty_pressure, diversity_pressure, domain_shift_pressure) >= 0.55:
        return "exploration"
    return "work"


def ensure_quest(
    tick: int,
    domain_hint: str | None = None,
    *,
    pressure_vector: Mapping[str, float] | None = None,
    plateau_streak: int = 0,
) -> tuple[dict[str, Any], bool]:
    quest = load_quest()
    if quest is None:
        quest = build_quest(
            choose_quest_type(pressure_vector, plateau_streak=plateau_streak),
            domain_hint=domain_hint,
            pressures=pressure_vector,
            tick=tick,
        )
        save_quest(quest)
        return quest, True

    age = tick - int(quest.get("tick_start", 0))
    ttl = int(quest.get("ttl_ticks", 4))
    if age >= ttl:
        quest = build_quest(
            choose_quest_type(pressure_vector, plateau_streak=plateau_streak),
            domain_hint=domain_hint,
            pressures=pressure_vector,
            tick=tick,
        )
        save_quest(quest)
        return quest, True

    return quest, False


def update_quest(
    quest: Mapping[str, Any],
    tick: int,
    best_score: float,
    last_metrics: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    updated = dict(quest)
    target = dict(updated.get("target", {}))
    min_score = float(target.get("min_score", 0.65))

    if best_score >= min_score:
        updated["wins"] = int(updated.get("wins", 0)) + 1
        target["min_score"] = round(min(0.95, min_score + 0.02), 3)
    else:
        updated["fails"] = int(updated.get("fails", 0)) + 1

    if last_metrics:
        target["min_novelty"] = round(max(target.get("min_novelty", 0.35), float(last_metrics.get("novelty", 0.0))), 3)
        target["min_diversity"] = round(max(target.get("min_diversity", 0.35), float(last_metrics.get("diversity", 0.0))), 3)

    updated["target"] = target
    updated["updated_at"] = now()
    updated["tick_last_seen"] = tick
    save_quest(updated)
    return updated
