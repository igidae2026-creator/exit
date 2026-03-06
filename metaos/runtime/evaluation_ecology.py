from __future__ import annotations

from typing import Any, Mapping, Sequence


def _avg(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _health(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def evaluation_ecology(history: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    rows = history[-32:] if history else ()
    novelty = [float(row.get("novelty", 0.0)) for row in rows if isinstance(row, Mapping)]
    diversity = [float(row.get("diversity", 0.0)) for row in rows if isinstance(row, Mapping)]
    cost = [float(row.get("cost", 0.0)) for row in rows if isinstance(row, Mapping)]
    fail_rate = [float(row.get("fail_rate", 0.0)) for row in rows if isinstance(row, Mapping)]
    lineage = [
        max(0.0, float((row.get("pressure", {}) if isinstance(row.get("pressure"), Mapping) else {}).get("diversity_pressure", 0.0)) - 0.5)
        for row in rows
    ]
    repair = [1.0 if row.get("repair") else 0.0 for row in rows if isinstance(row, Mapping)]
    exploration = [
        1.0
        if str((row.get("quest", {}) if isinstance(row.get("quest"), Mapping) else {}).get("type", "")) in {"exploration", "reframing"}
        else 0.0
        for row in rows
    ]
    return {
        "novelty_health": _health(_avg(novelty) / 0.35 if novelty else 0.5),
        "diversity_health": _health(_avg(diversity) / 0.4 if diversity else 0.5),
        "efficiency_health": _health(1.0 - (_avg(cost) + _avg(fail_rate))),
        "lineage_health": _health(1.0 - (_avg(lineage) * 1.2)),
        "repair_health": _health(1.0 - _avg(repair)),
        "exploration_health": _health(_avg(exploration)),
    }
