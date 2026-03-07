from __future__ import annotations

from typing import Any, Mapping


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, float(value))), 4)


def _qualifies(strategy_of_strategy: Mapping[str, Any], ecology: Mapping[str, Any], pressure: Mapping[str, float]) -> bool:
    exploration = float(strategy_of_strategy.get("exploration_emphasis", 0.0))
    diversification = float(strategy_of_strategy.get("diversification_emphasis", 0.0))
    recombination = float(strategy_of_strategy.get("recombination_emphasis", 0.0))
    domain_shift = float(pressure.get("domain_shift_pressure", 0.0))
    novelty = float(pressure.get("novelty_pressure", 0.0))
    diversity_health = float(ecology.get("diversity_health", 0.5))
    exploration_health = float(ecology.get("exploration_health", 0.5))
    domain_count = int(ecology.get("domain_count", 1) or 1)
    knowledge_flow = float(ecology.get("knowledge_flow", 0.0))
    return (
        (
            (exploration + diversification + recombination) >= 0.52
            and max(domain_shift, novelty) >= 0.55
            and min(diversity_health, exploration_health) <= 0.55
        )
        or (
            domain_count <= 2
            and (exploration + recombination) >= 0.25
            and (domain_shift + novelty) >= 0.5
        )
        or (
            domain_count <= 2
            and knowledge_flow >= 0.45
            and (exploration + diversification + recombination) >= 0.75
        )
    )


def domain_creation(
    strategy_of_strategy: Mapping[str, Any],
    ecology: Mapping[str, Any],
    pressure: Mapping[str, float],
) -> dict[str, Any] | None:
    strategy = dict(strategy_of_strategy or {})
    ecology_state = dict(ecology or {})
    pressure_state = dict(pressure or {})
    if not _qualifies(strategy, ecology_state, pressure_state):
        return None

    domain_count = max(1, int(ecology_state.get("domain_count", 1)))
    signature = int(
        round(
            1000
            * (
                float(strategy.get("exploration_emphasis", 0.0))
                + float(strategy.get("recombination_emphasis", 0.0))
                + float(pressure_state.get("domain_shift_pressure", 0.0))
            )
        )
    )
    name = f"meta_domain_{domain_count + 1}_{signature}"
    novelty_push = float(pressure_state.get("novelty_pressure", 0.0))
    diversity_push = 1.0 - float(ecology_state.get("diversity_health", 0.5))
    flow_push = float(ecology_state.get("knowledge_flow", 0.0))
    return {
        "name": name,
        "cluster": name.split("_")[0],
        "constraints": {
            "novelty": _clamp(0.45 + 0.35 * novelty_push),
            "cross_domain": _clamp(0.25 + 0.45 * flow_push),
            "diversity": _clamp(0.30 + 0.40 * diversity_push),
        },
        "evaluation_recipe": {
            "score": _clamp(0.72 + 0.16 * float(strategy.get("stabilization_emphasis", 0.0))),
            "novelty": _clamp(0.38 + 0.30 * novelty_push),
            "transfer": _clamp(0.28 + 0.40 * float(strategy.get("recombination_emphasis", 0.0))),
        },
        "mutation_priors": {
            "mutation_rate": _clamp(0.18 + 0.22 * float(strategy.get("exploration_emphasis", 0.0))),
            "recombination_rate": _clamp(0.14 + 0.24 * float(strategy.get("recombination_emphasis", 0.0))),
            "domain_shift_bias": _clamp(0.18 + 0.36 * float(pressure_state.get("domain_shift_pressure", 0.0))),
        },
        "source": {
            "strategy_of_strategy": strategy,
            "pressure": pressure_state,
        },
        "resource_contract": {
            "arbitration_weight": _clamp(0.30 + 0.50 * diversity_push),
            "migration_bias": _clamp(0.20 + 0.40 * flow_push),
        },
        "niche": "frontier" if novelty_push >= 0.6 else "bridge",
    }
