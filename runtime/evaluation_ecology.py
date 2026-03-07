from __future__ import annotations

from collections import Counter
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
    evaluation_counts: Counter[str] = Counter()
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        evaluation = row.get("evaluation", {}) if isinstance(row.get("evaluation"), Mapping) else {}
        regime = str(evaluation.get("regime", row.get("evaluation_regime", ""))).strip()
        if regime:
            evaluation_counts[regime] += 1
    total_evaluations = sum(evaluation_counts.values()) or 1
    evaluation_dominance = max((value / total_evaluations) for value in evaluation_counts.values()) if evaluation_counts else 0.0
    return {
        "novelty_health": _health(_avg(novelty) / 0.35 if novelty else 0.5),
        "diversity_health": _health(_avg(diversity) / 0.4 if diversity else 0.5),
        "efficiency_health": _health(1.0 - (_avg(cost) + _avg(fail_rate))),
        "lineage_health": _health(1.0 - (_avg(lineage) * 1.2)),
        "repair_health": _health(1.0 - _avg(repair)),
        "exploration_health": _health(_avg(exploration)),
        "evaluation_diversity": _health((1.0 - evaluation_dominance) + (0.25 * min(1.0, len(evaluation_counts) / 4.0))),
        "evaluation_dominance_index": _health(evaluation_dominance),
    }
