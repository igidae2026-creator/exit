from __future__ import annotations

from typing import Any, Mapping


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, float(value))), 4)


def self_tuning_guardrails(
    civilization: Mapping[str, Any],
    economy: Mapping[str, Any],
    stability: Mapping[str, Any],
) -> dict[str, Any]:
    civilization_state = dict(civilization or {})
    economy_state = dict(economy or {})
    stability_state = dict(stability or {})
    diversity_pressure = _clamp(0.35 + 0.30 * float(civilization_state.get("dominance_index", 0.0)))
    domain_expansion_rate = _clamp(0.20 + 0.40 * float(stability_state.get("underexploration_score", 0.0)) - 0.35 * float(stability_state.get("overexpansion_score", 0.0)))
    mutation_aggressiveness = _clamp(0.18 + 0.35 * float(stability_state.get("stagnation_score", 0.0)) - 0.25 * float(stability_state.get("drift_score", 0.0)))
    exploration_budget = _clamp(0.30 + 0.40 * float(stability_state.get("underexploration_score", 0.0)) + 0.10 * float(economy_state.get("economy_balance_score", 0.0)))
    repair_escalation = _clamp(0.22 + 0.45 * float(stability_state.get("drift_score", 0.0)))
    diversity_allocation_budget = _clamp(0.22 + 0.50 * float(civilization_state.get("dominance_index", 0.0)) + 0.20 * float(stability_state.get("underexploration_score", 0.0)))
    evaluation_diversity_budget = _clamp(
        0.24
        + 0.45 * float(civilization_state.get("evaluation_dominance_index", 0.0))
        + 0.25 * max(0.0, 1.0 - min(1.0, float(civilization_state.get("active_evaluation_generations", 0.0)) / 2.0))
    )
    actions: list[str] = []
    if diversity_pressure >= 0.55:
        actions.append("increase_diversity_pressure")
    if domain_expansion_rate <= 0.18:
        actions.append("throttle_domain_expansion")
    if mutation_aggressiveness <= 0.16:
        actions.append("reduce_mutation_rate")
    elif mutation_aggressiveness >= 0.48:
        actions.append("raise_exploration_mutation")
    if repair_escalation >= 0.5:
        actions.append("raise_repair_escalation")
    if float(stability_state.get("concentration_streak", 0.0)) >= 6:
        actions.extend(
            [
                "force_branching_pressure",
                "force_evaluation_diversification",
                "increase_dormant_activation_attempts",
            ]
        )
    if float(stability_state.get("evaluation_concentration_streak", 0.0)) >= 6 or float(civilization_state.get("active_evaluation_generations", 0.0)) <= 1.0:
        actions.extend(
            [
                "raise_evaluation_diversity_budget",
                "bias_evaluation_branching",
                "reduce_monopolistic_evaluation_dominance",
            ]
        )
    tuned = {
        "diversity_pressure": diversity_pressure,
        "domain_expansion_rate": domain_expansion_rate,
        "mutation_aggressiveness": mutation_aggressiveness,
        "exploration_budget": exploration_budget,
        "repair_escalation": repair_escalation,
        "diversity_allocation_budget": diversity_allocation_budget,
        "evaluation_diversity_budget": evaluation_diversity_budget,
    }
    return {
        "guardrail_state": {"bounded": True, "stable": float(stability_state.get("stability_score", 0.0)) >= 0.4},
        "tuned_thresholds": tuned,
        "guardrail_actions": actions[:8],
    }


__all__ = ["self_tuning_guardrails"]
