from __future__ import annotations

import math
from typing import Any, Callable, Mapping

from metaos.runtime.collapse_guard import detect_guard_state
from metaos.runtime.meta_cooldown import quest_cooldown
from signal.pressure import pressure_frame


def recent_state(guard_history: list[dict[str, Any]]) -> dict[str, int]:
    history = guard_history[-8:]
    rolling = guard_history[-32:]
    plateau_streak = sum(1 for row in history if float(row.get("domain_shift_pressure", row.get("pressure", {}).get("domain_shift_pressure", 0.0))) >= 0.7)
    novelty_low_streak = sum(1 for row in history if float(row.get("novelty", 1.0)) <= 0.25)
    lineage_high_streak = sum(1 for row in history if float(row.get("diversity_pressure", row.get("pressure", {}).get("diversity_pressure", 0.0))) >= 0.85)
    repair_cycle_streak = sum(1 for row in history if row.get("repair"))
    domains = [str(row.get("routing", {}).get("selected_domain", row.get("domain", "default"))) for row in history]
    routing_stagnation = len(history) if history and len(set(domains)) <= 1 else 0
    meta_repeat = 0
    reframing_repeat = 0
    repair_repeat = 0
    for row in reversed(history):
        quest = row.get("quest", {}) if isinstance(row.get("quest"), Mapping) else {}
        qtype = str(quest.get("type", ""))
        if not qtype:
            continue
        if qtype == "meta":
            meta_repeat += 1
        else:
            break
    for row in reversed(history):
        quest = row.get("quest", {}) if isinstance(row.get("quest"), Mapping) else {}
        qtype = str(quest.get("type", ""))
        if not qtype:
            continue
        if qtype == "reframing":
            reframing_repeat += 1
        else:
            break
    for row in reversed(history):
        quest = row.get("quest", {}) if isinstance(row.get("quest"), Mapping) else {}
        repair = row.get("repair")
        qtype = str(quest.get("type", ""))
        if not qtype and not repair:
            continue
        if qtype == "repair" or repair:
            repair_repeat += 1
        else:
            break
    guard_active = any(bool((row.get("guard", {}) if isinstance(row.get("guard"), Mapping) else {}).get(flag)) for row in history for flag in ("freeze_export", "downshift_workers", "force_reframing", "force_meta"))
    rolling_quests = [str((row.get("quest", {}) if isinstance(row.get("quest"), Mapping) else {}).get("type", "")) for row in rolling]
    rolling_quests = [qtype for qtype in rolling_quests if qtype]
    total = len(rolling_quests) or 1
    meta_share = sum(1 for qtype in rolling_quests if qtype == "meta") / total
    reframing_share = sum(1 for qtype in rolling_quests if qtype == "reframing") / total
    work_exploration_share = sum(1 for qtype in rolling_quests if qtype in {"work", "exploration"}) / total
    failed_reframing_repeat = 0
    for row in reversed(history):
        quest = row.get("quest", {}) if isinstance(row.get("quest"), Mapping) else {}
        qtype = str(quest.get("type", ""))
        pressure_row = row.get("pressure", {}) if isinstance(row.get("pressure"), Mapping) else {}
        if qtype != "reframing":
            break
        if (
            float(row.get("novelty", 1.0)) <= 0.25
            or float(pressure_row.get("novelty_pressure", 0.0)) >= 0.85
            or float(pressure_row.get("domain_shift_pressure", 0.0)) >= 0.45
        ):
            failed_reframing_repeat += 1
        else:
            break
    novelty_collapse_persist = (
        sum(1 for row in rolling if float(row.get("novelty", 1.0)) <= 0.25) >= max(3, math.ceil(len(rolling) * 0.25))
        if rolling
        else False
    )
    return {
        "plateau_streak": plateau_streak,
        "novelty_low_streak": novelty_low_streak,
        "lineage_high_streak": lineage_high_streak,
        "repair_cycle_streak": repair_cycle_streak,
        "routing_stagnation": routing_stagnation,
        "meta_repeat": meta_repeat,
        "reframing_repeat": reframing_repeat,
        "repair_repeat": repair_repeat,
        "guard_active": int(guard_active),
        "failed_reframing_repeat": failed_reframing_repeat,
        "meta_share": round(meta_share, 4),
        "reframing_share": round(reframing_share, 4),
        "work_exploration_share": round(work_exploration_share, 4),
        "novelty_collapse_persist": int(novelty_collapse_persist),
    }


def build_pressure_frame(
    metrics: Mapping[str, float],
    *,
    domain: str,
    history: list[Mapping[str, Any]],
    plateau_fn: Callable[[], bool],
    novelty_drop_fn: Callable[[], bool],
    concentration_fn: Callable[[], float],
) -> dict[str, Any]:
    raw_signal = pressure_frame(metrics)
    raw_pressure = dict(raw_signal["pressure"])
    plateau_hit = plateau_fn()
    lineage_high = concentration_fn() > 0.45
    novelty_low_sustained = novelty_drop_fn()
    preliminary_guard = detect_guard_state(history + [{"pressure": raw_pressure, "domain": domain, **dict(metrics)}])
    signal_frame = pressure_frame(metrics, history=history, guard=preliminary_guard)
    stabilized_pressure = dict(signal_frame["stabilized_pressure"])
    raw_market = dict(signal_frame["market"])
    guard_seed = history + [{"pressure": stabilized_pressure, "stabilized_pressure": stabilized_pressure, "domain": domain, **dict(metrics)}]
    recent = recent_state(guard_seed)
    guard = detect_guard_state(guard_seed)
    recent["guard_active"] = int(any(bool(guard.get(key)) for key in ("freeze_export", "downshift_workers", "force_reframing", "force_meta")))
    cooldown_state = quest_cooldown(recent)
    return {
        "pressure": raw_pressure,
        "stabilized_pressure": stabilized_pressure,
        "market": raw_market,
        "guard": guard,
        "recent_state": recent,
        "cooldown_state": cooldown_state,
        "history": history,
        "plateau_hit": plateau_hit,
        "lineage_high": lineage_high,
        "novelty_low_sustained": novelty_low_sustained,
    }


__all__ = ["build_pressure_frame", "recent_state"]
