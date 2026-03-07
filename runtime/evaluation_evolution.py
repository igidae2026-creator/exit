from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from artifact.registry import register_envelope, rows


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, float(value))), 4)


def _select_regime(
    activation_pressure: float,
    stagnation: float,
    diversity_deficit: float,
    domain_activation_gap: float,
    generation_index: int,
) -> str:
    regimes = ["novelty", "diversity", "efficiency", "coverage"]
    selector = int(round(activation_pressure * 10.0 + stagnation * 7.0 + diversity_deficit * 5.0 + domain_activation_gap * 3.0))
    return regimes[(generation_index + selector) % len(regimes)]


def evolve_evaluations(
    current: Mapping[str, Any] | None,
    pressure: Mapping[str, float],
    market_state: Mapping[str, Any] | None = None,
    *,
    parent: str | None = None,
) -> dict[str, Any]:
    current = dict(current or {})
    pressure = dict(pressure or {})
    market_state = dict(market_state or {})
    stagnation = float(market_state.get("policy_stagnation", 0.0) or 0.0)
    diversity_deficit = max(0.0, 0.5 - float(market_state.get("effective_lineage_diversity", market_state.get("lineage_diversity", 0.5)) or 0.5))
    domain_activation_gap = max(0.0, 0.45 - float(market_state.get("domain_activation_rate", 0.45) or 0.45))
    activation_pressure = _clamp(
        0.34 * stagnation
        + 0.26 * diversity_deficit
        + 0.20 * domain_activation_gap
        + 0.20 * float(pressure.get("novelty_pressure", 0.0))
    )
    prior = [row for row in rows() if str(row.get("artifact_type", row.get("type", ""))) == "evaluation_model"]
    evaluation_generation_count = len(prior) + 1
    regime = _select_regime(
        activation_pressure,
        stagnation,
        diversity_deficit,
        domain_activation_gap,
        evaluation_generation_count,
    )
    evaluation = {
        "regime": regime,
        "novelty_weight": _clamp(float(current.get("novelty_weight", 0.24)) + 0.10 * float(pressure.get("novelty_pressure", 0.0)) + (0.08 if regime == "novelty" else 0.0)),
        "diversity_weight": _clamp(float(current.get("diversity_weight", 0.22)) + 0.10 * float(pressure.get("diversity_pressure", 0.0)) + (0.08 if regime == "diversity" else 0.0)),
        "efficiency_weight": _clamp(float(current.get("efficiency_weight", 0.20)) + 0.08 * float(pressure.get("efficiency_pressure", 0.0)) + (0.08 if regime == "efficiency" else 0.0)),
        "repair_weight": _clamp(float(current.get("repair_weight", 0.12)) + 0.12 * float(pressure.get("repair_pressure", 0.0))),
        "coverage_weight": _clamp(float(current.get("coverage_weight", 0.18)) + (0.10 if regime == "coverage" else 0.02 * float(pressure.get("domain_shift_pressure", 0.0)))),
        "selection_bias": _clamp(float(market_state.get("selection_bias", current.get("selection_bias", 0.25))) + (0.05 if regime in {"diversity", "coverage"} else 0.0)),
        "activation_pressure": activation_pressure,
    }
    artifact_id = register_envelope(
        aclass="evaluation",
        atype="evaluation_model",
        spec={"evaluation": evaluation},
        refs={"parents": [parent] if parent else [], "inputs": [], "subjects": [], "context": {"pressure": pressure, "market": market_state}},
        provenance={
            "score": 1.0 - float(pressure.get("efficiency_pressure", 0.0)),
            "novelty": float(pressure.get("novelty_pressure", 0.0)),
            "diversity": float(pressure.get("diversity_pressure", 0.0)),
            "efficiency": 1.0 - float(pressure.get("repair_pressure", 0.0)),
        },
    )
    lineage_counter = Counter(
        str((((row.get("refs") or {}).get("parents") or ["root"])[0]))
        for row in prior
        if isinstance(row.get("refs"), Mapping)
    )
    regime_counter = Counter(
        str(((row.get("spec") or {}).get("evaluation") or {}).get("regime", "novelty"))
        for row in prior
        if isinstance(row.get("spec"), Mapping)
    )
    regime_counter[regime] += 1
    evaluation_turnover = round(min(1.0, evaluation_generation_count / max(1.0, len(lineage_counter) + 3.0)), 4)
    turnover_quality = _clamp(
        (0.45 * (1.0 - float(pressure.get("repair_pressure", 0.0))))
        + (0.30 * float(pressure.get("diversity_pressure", 0.0)))
        + (0.25 * float(pressure.get("novelty_pressure", 0.0)))
    )
    target_active = max(
        2,
        int(
            round(
                2
                + (3 * activation_pressure)
                + (2 * diversity_deficit)
                + (1 if float(market_state.get("evaluation_dominance_index", 1.0) or 1.0) > 0.72 else 0)
            )
        ),
    )
    active_generations = min(max(2, len(regime_counter)), max(2, target_active))
    evaluation_branch_rate = _clamp(0.45 * activation_pressure + 0.35 * diversity_deficit + 0.20 * stagnation)
    imported_external = int(market_state.get("imported_evaluation_generations", 0) or 0)
    adopted_external = int(market_state.get("adopted_evaluation_generations", 0) or 0)
    active_external = int(market_state.get("active_external_evaluation_generations", 0) or 0)
    active_distribution = {
        key: round(value / max(1.0, float(sum(regime_counter.values()) or 1)), 4)
        for key, value in sorted(regime_counter.items())
    }
    dominance = max(active_distribution.values(), default=0.0)
    evaluation_diversity = _clamp((1.0 - dominance) + (0.25 * min(1.0, len(regime_counter) / 4.0)))
    return {
        "artifact_id": artifact_id,
        "evaluation": evaluation,
        "evaluation_regime": regime,
        "lineage_parent": parent,
        "evaluation_generation_count": evaluation_generation_count,
        "evaluation_turnover": evaluation_turnover,
        "active_evaluation_generations": active_generations,
        "dormant_evaluation_generations": max(0, len(regime_counter) - active_generations),
        "retired_evaluation_generations": max(0, len(prior) - len(regime_counter)),
        "evaluation_turnover_quality": turnover_quality,
        "evaluation_stagnation": _clamp(1.0 - turnover_quality),
        "evaluation_branch_rate": evaluation_branch_rate,
        "evaluation_diversity": evaluation_diversity,
        "evaluation_dominance_index": round(dominance, 4),
        "evaluation_retirement_rate": _clamp(max(0.0, 0.12 - (0.08 * activation_pressure))),
        "evaluation_reactivation_rate": _clamp(0.20 + (0.50 * activation_pressure)),
        "active_evaluation_distribution": active_distribution,
        "imported_evaluation_generations": imported_external,
        "adopted_evaluation_generations": adopted_external,
        "active_external_evaluation_generations": active_external,
    }


__all__ = ["evolve_evaluations"]
