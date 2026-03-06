from __future__ import annotations

from typing import Any, Mapping

from metaos.runtime.civilization_selection import civilization_select


def candidate_summaries(
    pressure: Mapping[str, float],
    market_state: Mapping[str, float],
    ecology: Mapping[str, float],
) -> list[dict[str, Any]]:
    novelty_gap = 1.0 - float(ecology.get("novelty_health", 0.5))
    diversity_gap = 1.0 - float(ecology.get("diversity_health", 0.5))
    exploration_gap = 1.0 - float(ecology.get("exploration_health", 0.5))
    repair_gap = 1.0 - float(ecology.get("repair_health", 0.5))
    return [
        {"type": "strategy", "base_score": 0.22 + 0.06 * float(market_state.get("mutation_bias", 0.0)) + 0.03 * novelty_gap},
        {"type": "policy", "base_score": 0.32 + 0.08 * float(ecology.get("efficiency_health", 0.5)) + 0.05 * float(ecology.get("lineage_health", 0.5))},
        {"type": "evaluation", "base_score": 0.35 + 0.22 * novelty_gap + 0.12 * diversity_gap},
        {"type": "exploration_strategy", "base_score": 0.18 + 0.08 * exploration_gap + 0.04 * float(pressure.get("novelty_pressure", 0.0))},
        {"type": "strategy_of_strategy", "base_score": 0.24 + 0.22 * exploration_gap + 0.12 * float(pressure.get("domain_shift_pressure", 0.0))},
        {"type": "domain", "base_score": 0.36 + 0.34 * diversity_gap + 0.18 * float(pressure.get("domain_shift_pressure", 0.0))},
        {"type": "repair", "base_score": 0.28 + 0.14 * float(pressure.get("repair_pressure", 0.0)) + 0.08 * repair_gap},
        {"type": "allocator", "base_score": 0.3 + 0.08 * float(market_state.get("selection_bias", 0.0)) + 0.06 * float(ecology.get("efficiency_health", 0.5))},
    ]


def governed_selection(
    selection: Mapping[str, Any],
    population: Mapping[str, Any],
    governance: Mapping[str, Any],
    *,
    tick: int,
) -> dict[str, Any]:
    out = {
        "selected_artifact_type": str(selection.get("selected_artifact_type", "policy")),
        "selection_scores": dict(selection.get("selection_scores", {})) if isinstance(selection.get("selection_scores"), Mapping) else {},
    }
    if not bool(governance.get("intervention")):
        return out
    population_counts = dict(population.get("population_counts", {})) if isinstance(population.get("population_counts"), Mapping) else {}
    total = sum(int(value) for value in population_counts.values()) or 1
    dominant_type = max(population_counts, key=population_counts.get, default="")
    dominant_share = float(population_counts.get(dominant_type, 0)) / total if dominant_type else 0.0
    if dominant_share <= 0.60 or out["selected_artifact_type"] != dominant_type:
        return out
    alternates = ["policy", "evaluation", "strategy_of_strategy", "domain"]
    alternates = [name for name in alternates if name != dominant_type]
    selected = alternates[tick % len(alternates)]
    scores = dict(out["selection_scores"])
    scores[selected] = round(max(scores.values(), default=0.5) + 0.0001, 4)
    out["selected_artifact_type"] = selected
    out["selection_scores"] = scores
    return out


def build_selection_frame(
    stabilized_pressure: Mapping[str, float],
    stabilized_market: Mapping[str, float],
    ecology: Mapping[str, float],
    population: Mapping[str, Any],
    governance: Mapping[str, Any],
    *,
    tick: int,
) -> dict[str, Any]:
    selection = civilization_select(candidate_summaries(stabilized_pressure, stabilized_market, ecology), stabilized_pressure, stabilized_market, ecology)
    return {"civilization_selection": governed_selection(selection, population, governance, tick=tick)}


__all__ = ["build_selection_frame", "candidate_summaries", "governed_selection"]
