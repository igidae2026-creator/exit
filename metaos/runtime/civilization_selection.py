from __future__ import annotations

from typing import Any, Mapping, Sequence


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 4)


def civilization_select(
    candidates: Sequence[Mapping[str, Any]],
    pressure: Mapping[str, float],
    market: Mapping[str, float],
    ecology: Mapping[str, float],
) -> dict[str, Any]:
    pressure = dict(pressure or {})
    market = dict(market or {})
    ecology = dict(ecology or {})
    scores: dict[str, float] = {}
    for candidate in candidates:
        artifact_type = str(candidate.get("type", "policy"))
        base = float(candidate.get("base_score", candidate.get("score", 0.5)))
        novelty = float(pressure.get("novelty_pressure", 0.0))
        diversity = float(pressure.get("diversity_pressure", 0.0))
        domain_shift = float(pressure.get("domain_shift_pressure", 0.0))
        repair = float(pressure.get("repair_pressure", 0.0))
        novelty_gap = 1.0 - float(ecology.get("novelty_health", 0.5))
        diversity_gap = 1.0 - float(ecology.get("diversity_health", 0.5))
        exploration_gap = 1.0 - float(ecology.get("exploration_health", 0.5))
        repair_gap = 1.0 - float(ecology.get("repair_health", 0.5))
        if artifact_type == "policy":
            score = base + 0.16 * float(ecology.get("efficiency_health", 0.5)) + 0.12 * float(ecology.get("lineage_health", 0.5)) - 0.12 * novelty - 0.08 * domain_shift
        elif artifact_type == "evaluation":
            score = base + 0.34 * novelty_gap + 0.12 * diversity_gap
        elif artifact_type == "strategy_of_strategy":
            score = base + 0.28 * exploration_gap + 0.15 * domain_shift + 0.08 * float(market.get("mutation_bias", 0.0))
        elif artifact_type == "domain":
            score = base + 0.3 * domain_shift + 0.42 * diversity_gap + 0.1 * diversity
        elif artifact_type == "repair":
            score = base + 0.4 * repair + 0.2 * repair_gap
        elif artifact_type == "allocator":
            score = base + 0.16 * float(market.get("selection_bias", 0.0)) + 0.08 * float(ecology.get("efficiency_health", 0.5))
        else:
            score = base + 0.12 * novelty + 0.12 * diversity
        scores[artifact_type] = _clamp(score)
    selected = max(scores, key=scores.get) if scores else "policy"
    return {"selected_artifact_type": selected, "selection_scores": scores}
