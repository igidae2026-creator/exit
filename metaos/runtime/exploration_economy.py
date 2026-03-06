from __future__ import annotations

from typing import Any, Mapping


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, float(value))), 4)


def exploration_economy(state: Mapping[str, Any]) -> dict[str, float]:
    pressure = dict(state.get("pressure", {})) if isinstance(state.get("pressure"), Mapping) else {}
    market = dict(state.get("market", {})) if isinstance(state.get("market"), Mapping) else {}
    ecology = dict(state.get("ecology", {})) if isinstance(state.get("ecology"), Mapping) else {}
    population = dict(state.get("population", {})) if isinstance(state.get("population"), Mapping) else {}
    population_counts = dict(population.get("population_counts", {})) if isinstance(population.get("population_counts"), Mapping) else {}
    growth_rates = dict(population.get("growth_rates", {})) if isinstance(population.get("growth_rates"), Mapping) else {}

    domain_pressure = float(pressure.get("domain_shift_pressure", 0.0))
    novelty_pressure = float(pressure.get("novelty_pressure", 0.0))
    selection_bias = float(market.get("selection_bias", 0.0))
    diversity_gap = 1.0 - float(ecology.get("diversity_health", 0.5))
    exploration_gap = 1.0 - float(ecology.get("exploration_health", 0.5))
    domain_growth = float(growth_rates.get("domain", 0.0))
    policy_growth = float(growth_rates.get("policy", 0.0))
    evaluation_risk = float((population.get("extinction_risk", {}) if isinstance(population.get("extinction_risk"), Mapping) else {}).get("evaluation", 0.0))

    exploration_budget = _clamp(0.34 + 0.16 * novelty_pressure + 0.18 * exploration_gap - 0.12 * selection_bias)
    recombination_budget = _clamp(0.18 + 0.20 * domain_pressure + 0.16 * diversity_gap - 0.10 * max(0.0, domain_growth))
    policy_budget = _clamp(0.16 + 0.12 * max(0.0, 0.18 - policy_growth) + 0.10 * float(population_counts.get("policy", 0) == 0))
    evaluation_budget = _clamp(0.16 + 0.18 * evaluation_risk + 0.12 * diversity_gap)
    return {
        "exploration_budget": exploration_budget,
        "recombination_budget": recombination_budget,
        "policy_budget": policy_budget,
        "evaluation_budget": evaluation_budget,
    }
