from __future__ import annotations

from typing import Any, Mapping


def should_reframe(
    pressure: Mapping[str, float],
    *,
    plateau_hit: bool = False,
    lineage_high: bool = False,
    novelty_low_sustained: bool = False,
) -> bool:
    return (
        plateau_hit
        or lineage_high
        or novelty_low_sustained
        or float(pressure.get("reframing_pressure", 0.0)) > 0.70
    )


def spawn_quest(
    pressure: Mapping[str, float],
    *,
    plateau_hit: bool = False,
    lineage_high: bool = False,
    novelty_low_sustained: bool = False,
) -> dict[str, Any]:
    if float(pressure["repair_pressure"]) > 0.75:
        return {"type": "repair", "priority": "high"}
    if should_reframe(
        pressure,
        plateau_hit=plateau_hit,
        lineage_high=lineage_high,
        novelty_low_sustained=novelty_low_sustained,
    ):
        return {"type": "reframing", "priority": "high"}
    if float(pressure["domain_shift_pressure"]) > 0.70:
        return {"type": "meta", "priority": "high"}
    if float(pressure["diversity_pressure"]) > 0.70:
        return {"type": "exploration", "mode": "diversify"}
    if float(pressure["novelty_pressure"]) > 0.60:
        return {"type": "exploration", "mode": "novelty"}
    return {"type": "work", "priority": "normal"}
