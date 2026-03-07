from __future__ import annotations

from typing import Any, Mapping, Sequence

from runtime.ceiling_metrics import latest_ceiling_metrics
from runtime.environment_pressure import latest_environment_signals


def _ratio(values: Mapping[str, Any]) -> float:
    total = sum(max(0.0, float(value)) for value in values.values())
    if total <= 0.0:
        return 0.0
    top = max(max(0.0, float(value)) for value in values.values())
    return min(1.0, top / total)


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 4)


def _recent_signal(recent_truth: Sequence[Mapping[str, Any]] | None, key: str) -> float:
    rows = list(recent_truth or [])[-16:]
    if not rows:
        return 0.0
    values: list[float] = []
    for row in rows:
        if isinstance(row.get(key), (int, float)):
            values.append(float(row.get(key)))
            continue
        nested = row.get("pressure", {}) if isinstance(row.get("pressure"), Mapping) else {}
        if isinstance(nested.get(key), (int, float)):
            values.append(float(nested.get(key)))
    if not values:
        return 0.0
    return sum(values) / len(values)


def pressure_frame(civilization_state: Mapping[str, Any], recent_truth: Sequence[Mapping[str, Any]] | None = None) -> dict[str, float]:
    artifact_population = dict(civilization_state.get("artifact_population", {})) if isinstance(civilization_state.get("artifact_population"), Mapping) else {}
    lineage_population = dict(civilization_state.get("lineage_population", {})) if isinstance(civilization_state.get("lineage_population"), Mapping) else {}
    domain_population = dict(civilization_state.get("domain_population", {})) if isinstance(civilization_state.get("domain_population"), Mapping) else {}
    policy_population = dict(civilization_state.get("policy_population", {})) if isinstance(civilization_state.get("policy_population"), Mapping) else {}
    knowledge_density = float(civilization_state.get("knowledge_density", 0.0))
    memory_growth = float(civilization_state.get("memory_growth", 0.0))
    exploration_budget = max(1.0, float(civilization_state.get("exploration_budget", 1) or 1))
    artifact_total = sum(max(0.0, float(value)) for value in artifact_population.values())
    domain_total = sum(max(0.0, float(value)) for value in domain_population.values())
    lineage_total = sum(max(0.0, float(value)) for value in lineage_population.values())
    policy_generations = float(policy_population.get("generations", civilization_state.get("policy_generations", 0)) or 0.0)
    recent_repair = _recent_signal(recent_truth, "repair_pressure")
    recent_novelty = _recent_signal(recent_truth, "novelty")
    recent_fail = _recent_signal(recent_truth, "fail_rate")
    budget_exhausted = float(bool(civilization_state.get("budget_exhausted", False)))
    ceiling = latest_ceiling_metrics(recent_truth)
    environment = latest_environment_signals(recent_truth)
    novelty_pressure = _clamp(
        0.52
        - (0.18 * knowledge_density)
        - (0.08 * memory_growth)
        + (0.08 * (1.0 - min(1.0, policy_generations / 32.0)))
        + (0.05 * (1.0 - recent_novelty))
        + (0.10 * float(ceiling.get("policy_staleness_score", 0.0)))
        + (0.10 * float(environment.get("competition_pressure", 0.0)))
    )
    diversity_pressure = _clamp(
        (0.48 * _ratio(lineage_population))
        + (0.15 * float(lineage_total <= 1.0))
        + (0.10 * float(domain_total <= 2.0))
        + (0.12 * float(ceiling.get("portfolio_concentration_risk", 0.0)))
        + (0.08 * float(environment.get("platform_policy_pressure", 0.0)))
    )
    efficiency_pressure = _clamp(
        (0.18 * memory_growth)
        + (0.18 * min(1.0, artifact_total / max(1.0, exploration_budget * 4.0)))
        + (0.16 * budget_exhausted)
        + (0.10 * float(environment.get("environment_volatility", 0.0)))
        + (0.08 * float(ceiling.get("dominant_lock_in_risk", 0.0)))
    )
    repair_pressure = _clamp(0.12 + (0.30 * recent_fail) + (0.22 * recent_repair) + (0.16 * float(memory_growth > 0.9 and knowledge_density < 0.45)))
    domain_shift_pressure = _clamp(
        (0.24 * novelty_pressure)
        + (0.20 * diversity_pressure)
        + (0.10 * float(domain_total <= 2.0))
        + (0.08 * budget_exhausted)
        + (0.18 * float(environment.get("market_adoption_pressure", 0.0)))
        + (0.10 * float(ceiling.get("threshold_crossing_score", 0.0)))
    )
    reframing_pressure = _clamp(
        (0.20 * novelty_pressure)
        + (0.16 * diversity_pressure)
        + (0.12 * repair_pressure)
        + (0.10 * float(exploration_budget <= 3.0))
        + (0.14 * float(environment.get("audience_feedback_pressure", 0.0)))
        + (0.14 * float(ceiling.get("breakout_acceleration_score", 0.0)))
    )
    return {
        "novelty_pressure": novelty_pressure,
        "diversity_pressure": diversity_pressure,
        "efficiency_pressure": efficiency_pressure,
        "repair_pressure": repair_pressure,
        "domain_shift_pressure": domain_shift_pressure,
        "reframing_pressure": reframing_pressure,
        **{key: round(float(value), 4) for key, value in ceiling.items()},
        **{key: round(float(value), 4) for key, value in environment.items()},
    }


__all__ = ["pressure_frame"]
