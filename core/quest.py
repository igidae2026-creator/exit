from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Mapping

QUEST_PATH = "state/quest.json"
QUEST_TYPES = ("work", "exploration", "meta", "reframing", "transfer")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_quest(path: str | None = None) -> dict[str, Any] | None:
    target = path or QUEST_PATH
    if not os.path.exists(target):
        return None
    try:
        with open(target, "r", encoding="utf-8") as handle:
            row = json.load(handle)
    except Exception:
        return None
    return row if isinstance(row, dict) else None


def save_quest(quest: Mapping[str, Any], path: str | None = None) -> None:
    target = path or QUEST_PATH
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    tmp = f"{target}.tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(dict(quest), handle, ensure_ascii=False, indent=2)
    os.replace(tmp, target)


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
    pressure_snapshot = dict(pressures or {})
    return {
        "id": str(uuid.uuid4()),
        "quest_type": quest_type,
        "title": title or f"{quest_type.title()} quest",
        "description": description or f"Advance the {quest_type} frontier.",
        "created_at": now(),
        "domain_hint": domain_hint,
        "target": {
            "min_score": 0.55 if quest_type == "work" else 0.48,
            "min_novelty": 0.52 if quest_type in {"exploration", "reframing", "transfer"} else 0.30,
            "min_diversity": 0.50 if quest_type in {"exploration", "reframing", "transfer"} else 0.30,
            "min_usefulness": 0.42,
            "min_persistence": 0.36,
        },
        "ttl_ticks": ttl_ticks if ttl_ticks is not None else (4 if quest_type == "work" else 3),
        "tick_start": tick,
        "wins": 0,
        "fails": 0,
        "pressure_snapshot": pressure_snapshot,
    }


def default_quest(domain_hint: str | None = None, quest_type: str = "work") -> dict[str, Any]:
    return build_quest(quest_type, domain_hint=domain_hint)


def choose_quest_type(pressure_vector: Mapping[str, float] | None, *, plateau_streak: int = 0) -> str:
    pressure_vector = dict(pressure_vector or {})
    repair_pressure = float(pressure_vector.get("repair_pressure", 0.0))
    novelty_pressure = float(pressure_vector.get("novelty_pressure", 0.0))
    diversity_pressure = float(pressure_vector.get("diversity_pressure", 0.0))
    domain_shift_pressure = float(pressure_vector.get("domain_shift_pressure", 0.0))
    reframing_pressure = float(pressure_vector.get("reframing_pressure", 0.0))
    transfer_pressure = float(pressure_vector.get("transfer_pressure", 0.0))

    if reframing_pressure >= 0.7:
        return "reframing"
    if transfer_pressure >= 0.6:
        return "transfer"
    if repair_pressure >= 0.75:
        return "meta"
    if plateau_streak >= 2 or max(novelty_pressure, diversity_pressure, domain_shift_pressure) >= 0.55:
        return "exploration"
    return "work"


def ensure_quest(
    tick: int,
    domain_hint: str | None = None,
    *,
    pressure_vector: Mapping[str, float] | None = None,
    plateau_streak: int = 0,
    path: str | None = None,
) -> tuple[dict[str, Any], bool]:
    quest = load_quest(path)
    quest_type = choose_quest_type(pressure_vector, plateau_streak=plateau_streak)
    if quest is None:
        quest = build_quest(quest_type, domain_hint=domain_hint, pressures=pressure_vector, tick=tick)
        save_quest(quest, path)
        return quest, True
    age = tick - int(quest.get("tick_start", 0))
    ttl = int(quest.get("ttl_ticks", 4))
    should_rotate = age >= ttl or quest.get("quest_type") != quest_type
    if should_rotate:
        quest = build_quest(quest_type, domain_hint=domain_hint, pressures=pressure_vector, tick=tick)
        save_quest(quest, path)
        return quest, True
    return quest, False


def update_quest(quest: Mapping[str, Any], tick: int, best_score: float, last_metrics: Mapping[str, float] | None = None, path: str | None = None) -> dict[str, Any]:
    updated = dict(quest)
    target = dict(updated.get("target", {}))
    if best_score >= float(target.get("min_score", 0.65)):
        updated["wins"] = int(updated.get("wins", 0)) + 1
    else:
        updated["fails"] = int(updated.get("fails", 0)) + 1
    if last_metrics:
        for key, target_key in (("novelty", "min_novelty"), ("diversity", "min_diversity"), ("usefulness", "min_usefulness"), ("persistence", "min_persistence")):
            target[target_key] = round(max(float(target.get(target_key, 0.0)), float(last_metrics.get(key, 0.0))), 6)
    updated["target"] = target
    updated["updated_at"] = now()
    updated["tick_last_seen"] = tick
    save_quest(updated, path)
    return updated
