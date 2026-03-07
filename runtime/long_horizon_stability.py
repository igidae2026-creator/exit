from __future__ import annotations

from typing import Any, Mapping, Sequence

from runtime.stability_tuning import tune_stability


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, float(value))), 4)


def long_horizon_stability(
    civilization: Mapping[str, Any],
    economy: Mapping[str, Any],
    lineage: Mapping[str, Any],
    *,
    history: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    civilization_state = dict(civilization or {})
    economy_state = dict(economy or {})
    lineage_state = dict(lineage or {})
    rows = list(history or [])
    knowledge_density = float(civilization_state.get("knowledge_density", 0.0))
    memory_growth = float(civilization_state.get("memory_growth", 0.0))
    dominance = float(lineage_state.get("dominance_index", civilization_state.get("dominance_index", 0.0)))
    active_domains = int(civilization_state.get("active_domain_count", 0))
    created_domains = int(civilization_state.get("created_domain_count", active_domains))
    policy_stagnation = float(civilization_state.get("policy_stagnation", 0.0))
    evaluation_stagnation = float(civilization_state.get("evaluation_stagnation", 0.0))
    concentration_streak = float(civilization_state.get("concentration_streak", 0.0))
    active_evaluation_generations = float(civilization_state.get("active_evaluation_generations", 0.0))
    evaluation_dominance_index = float(civilization_state.get("evaluation_dominance_index", 0.0))
    balance = float(economy_state.get("economy_balance_score", 0.0))
    budget_skew = float(economy_state.get("budget_skew", 1.0))
    replay_window = max(1, len(rows))
    silent_window = sum(
        1
        for row in rows[-16:]
        if not any(row.get(key) for key in ("policy", "evaluation", "repair", "meta_exploration"))
    )
    evaluation_concentration_streak = 0
    for row in reversed(rows[-24:]):
        evaluation = row.get("evaluation", {}) if isinstance(row.get("evaluation"), Mapping) else {}
        regime = str(evaluation.get("regime", row.get("evaluation_regime", ""))).strip()
        if regime in {"", "novelty"}:
            evaluation_concentration_streak += 1
        else:
            break
    drift_score = _clamp(
        0.30 * max(0.0, 1.0 - knowledge_density)
        + 0.20 * max(0.0, 0.2 - memory_growth)
        + 0.25 * budget_skew
        + 0.25 * dominance
    )
    stagnation_score = _clamp(
        0.30 * policy_stagnation
        + 0.30 * evaluation_stagnation
        + 0.18 * max(0.0, 1.0 - balance)
        + 0.10 * (silent_window / 16.0)
        + 0.12 * max(0.0, 1.0 - min(1.0, active_evaluation_generations / 2.0))
    )
    overexpansion_score = _clamp(
        0.45 * max(0.0, budget_skew - 0.4)
        + 0.35 * max(0.0, (created_domains - max(2, active_domains)) / max(1.0, float(created_domains or 1)))
        + 0.20 * max(0.0, 1.0 - balance)
    )
    underexploration_score = _clamp(
        0.35 * max(0.0, 0.45 - float(civilization_state.get("lineage_survival_rate", 0.0)))
        + 0.35 * max(0.0, 0.4 - float(civilization_state.get("domain_activation_rate", 0.0)))
        + 0.20 * stagnation_score
        + 0.10 * min(1.0, concentration_streak / 12.0)
    )
    stability_score = _clamp(
        1.0
        - (
            0.28 * drift_score
            + 0.28 * stagnation_score
            + 0.22 * overexpansion_score
            + 0.22 * underexploration_score
        )
    )
    tuning = tune_stability(
        {
            "drift_score": drift_score,
            "stagnation_score": stagnation_score,
            "overexpansion_score": overexpansion_score,
            "underexploration_score": underexploration_score,
            "concentration_streak": concentration_streak,
        }
    )
    actions = list(dict.fromkeys(list(tuning.get("stability_actions", []))))
    if replay_window >= 32 and silent_window >= 8:
        actions.append("silent_collapse_review")
    if concentration_streak >= 6:
        actions.extend(
            [
                "force_branching_pressure",
                "force_evaluation_diversification",
                "increase_dormant_activation_attempts",
            ]
        )
    if active_evaluation_generations <= 1 or evaluation_concentration_streak >= 6 or evaluation_dominance_index > 0.78:
        actions.extend(
            [
                "bias_evaluation_plurality",
                "allocate_evaluation_diversity_budget",
                "reduce_evaluation_monopoly",
            ]
        )
    return {
        "stability_score": stability_score,
        "drift_score": drift_score,
        "stagnation_score": stagnation_score,
        "overexpansion_score": overexpansion_score,
        "underexploration_score": underexploration_score,
        "concentration_streak": int(concentration_streak),
        "evaluation_concentration_streak": int(evaluation_concentration_streak),
        "stability_actions": actions[:8],
        "bounded": True,
    }


__all__ = ["long_horizon_stability"]
