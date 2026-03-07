from __future__ import annotations

from typing import Any, Mapping

from runtime.civilization_state import civilization_state as build_civilization_state
from runtime.memory_pressure import memory_pressure


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, float(value))), 4)


def _budget_frame(
    exploration_budget: int,
    mutation_budget: float,
    selection_budget_units: int,
    policy_budget: int,
    evaluation_budget: int,
    domain_expansion_budget: int,
    repair_budget: int,
    diversity_allocation_budget: int,
    evaluation_diversity_budget: int,
) -> dict[str, float]:
    frame = {
        "exploration_budget": float(exploration_budget),
        "mutation_budget": float(max(1.0, round(1.0 + (4.0 * mutation_budget), 4))),
        "selection_budget": float(selection_budget_units),
        "policy_budget": float(policy_budget),
        "evaluation_budget": float(evaluation_budget),
        "domain_expansion_budget": float(domain_expansion_budget),
        "repair_budget": float(repair_budget),
        "diversity_allocation_budget": float(diversity_allocation_budget),
        "evaluation_diversity_budget": float(evaluation_diversity_budget),
    }
    total = sum(frame.values()) or 1.0
    return {key: round(value / total, 4) for key, value in frame.items()}


def allocate_resources(
    pressure: Mapping[str, float],
    ecology: Mapping[str, Any],
    population: Mapping[str, Any],
    manager_state: Mapping[str, Any] | None = None,
    memory_state: Mapping[str, float] | None = None,
    civilization_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    pressure_state = dict(pressure or {})
    ecology_state = dict(ecology or {})
    population_state = dict(population or {})
    manager_state = dict(manager_state or {})
    civilization_frame = dict(civilization_state or {})
    population_counts = dict(population_state.get("population_counts", {})) if isinstance(population_state.get("population_counts"), Mapping) else {}
    growth_rates = dict(population_state.get("growth_rates", {})) if isinstance(population_state.get("growth_rates"), Mapping) else {}
    extinction_risk = dict(population_state.get("extinction_risk", {})) if isinstance(population_state.get("extinction_risk"), Mapping) else {}
    memory_state = dict(memory_state or memory_pressure())
    novelty = float(pressure_state.get("novelty_pressure", 0.0))
    diversity = float(pressure_state.get("diversity_pressure", 0.0))
    efficiency = float(pressure_state.get("efficiency_pressure", 0.0))
    repair = float(pressure_state.get("repair_pressure", 0.0))
    domain_shift = float(pressure_state.get("domain_shift_pressure", 0.0))
    reframing = float(pressure_state.get("reframing_pressure", 0.0))
    competition = float(pressure_state.get("competition_pressure", 0.0))
    adoption = float(pressure_state.get("market_adoption_pressure", 0.0))
    platform = float(pressure_state.get("platform_policy_pressure", 0.0))
    volatility = float(pressure_state.get("environment_volatility", 0.0))
    breakout = float(pressure_state.get("breakout_acceleration_score", 0.0))
    concentration_risk = float(pressure_state.get("portfolio_concentration_risk", 0.0))
    domain_population = dict(civilization_frame.get("domain_population", {})) if isinstance(civilization_frame.get("domain_population"), Mapping) else {}
    domain_count = max(1, len(domain_population))
    dominance_index = float(civilization_frame.get("dominance_index", 0.0) or 0.0)
    evaluation_dominance_index = float(civilization_frame.get("evaluation_dominance_index", 0.0) or 0.0)
    active_evaluation_generations = int(civilization_frame.get("active_evaluation_generations", 0) or 0)
    exploration_gap = 1.0 - float(ecology_state.get("exploration_health", 0.5))
    diversity_gap = 1.0 - float(ecology_state.get("diversity_health", 0.5))
    evaluation_gap = 1.0 - float(ecology_state.get("evaluation_diversity", civilization_frame.get("evaluation_diversity", 0.5)) or 0.5)
    attention_budget = _clamp(0.28 + 0.18 * novelty + 0.10 * reframing + 0.08 * exploration_gap + 0.08 * competition + 0.06 * breakout)
    mutation_budget = _clamp(0.22 + 0.14 * novelty + 0.12 * domain_shift + 0.08 * diversity_gap - 0.06 * repair + 0.08 * volatility + 0.06 * platform)
    selection_weights = {
        "strategy": _clamp(0.18 + 0.10 * novelty),
        "policy": _clamp(0.16 + 0.10 * float(population_counts.get("policy", 0) == 0) + 0.05 * memory_state["knowledge_density"]),
        "quest": _clamp(0.14 + 0.10 * reframing + 0.12 * repair),
        "evaluation": _clamp(0.16 + 0.10 * float(extinction_risk.get("evaluation", 0.0)) + 0.04 * diversity_gap),
        "allocator": _clamp(0.12 + 0.10 * efficiency + 0.06 * memory_state["archive_pressure"]),
        "domain_genome": _clamp(0.16 + 0.12 * domain_shift + 0.08 * max(0.0, -float(growth_rates.get("domain", 0.0)))),
    }
    total = sum(selection_weights.values()) or 1.0
    selection_weights = {key: round(value / total, 4) for key, value in selection_weights.items()}
    runtime_bonus = int(manager_state.get("runtime_slot_bonus", 0) or 0)
    runtime_slot_allocation = {
        "runtime_slots": max(3, int(round(4 + (8 * attention_budget))) + runtime_bonus),
        "exploration_slots": max(1, int(round(1 + (5 * mutation_budget)))),
        "memory_slots": max(1, int(round(1 + (4 * memory_state["knowledge_density"])))),
        "repair_slots": max(1, int(round(1 + (4 * repair)))),
    }
    exploration_budget = max(3, int(round(3 + 4 * attention_budget + 3 * mutation_budget + 2 * domain_shift + 2 * competition + breakout)))
    selection_budget = _clamp(0.24 + 0.18 * efficiency + 0.14 * diversity + 0.10 * memory_state["knowledge_density"])
    domain_expansion_budget = max(0, int(round((2.0 * domain_shift) + (1.5 * novelty) + adoption - (0.4 * max(0, domain_count - 2)) + concentration_risk)))
    policy_budget = max(1, int(round(2 + (4 * novelty) + (3 * diversity))))
    evaluation_budget = max(1, int(round(2 + (3 * efficiency) + (2 * repair) + (2 * evaluation_gap))))
    repair_budget = max(1, int(round(1 + (4 * repair) + (2 * reframing) + (2 * platform) + volatility)))
    diversity_allocation_budget = max(1, int(round(1 + (4 * max(0.0, dominance_index - 0.45)) + (3 * diversity_gap))))
    evaluation_diversity_budget = max(
        1,
        int(
            round(
                1
                + (4 * max(0.0, evaluation_dominance_index - 0.45))
                + (3 * max(0.0, 2 - active_evaluation_generations))
                + (2 * evaluation_gap)
            )
        ),
    )
    selection_budget_units = max(1, int(round(2 + (5 * selection_budget))))
    budget_exhausted = exploration_budget <= 3
    budget_mix = _budget_frame(
        exploration_budget,
        mutation_budget,
        selection_budget_units,
        policy_budget,
        evaluation_budget,
        domain_expansion_budget,
        repair_budget,
        diversity_allocation_budget,
        evaluation_diversity_budget,
    )
    ideal = 1.0 / float(len(budget_mix))
    budget_skew = _clamp(sum(abs(value - ideal) for value in budget_mix.values()) / 2.0)
    economy_balance_score = _clamp(1.0 - budget_skew)
    rebalancing_actions: list[str] = []
    if budget_mix["domain_expansion_budget"] > 0.24:
        rebalancing_actions.append("reduce_domain_expansion_budget")
    if budget_mix["exploration_budget"] < 0.16:
        rebalancing_actions.append("increase_exploration_budget")
    if budget_mix["repair_budget"] < 0.08 and repair > 0.35:
        rebalancing_actions.append("increase_repair_budget")
    if budget_mix["selection_budget"] > 0.25 and diversity < 0.35:
        rebalancing_actions.append("shift_from_selection_to_mutation")
    if dominance_index > 0.7:
        rebalancing_actions.extend(
            [
                "raise_diversity_budget",
                "penalize_dominant_lineage_selection",
                "bias_branching_and_evaluation_mutation",
            ]
        )
    if active_evaluation_generations <= 1 or evaluation_dominance_index > 0.72:
        rebalancing_actions.extend(
            [
                "raise_evaluation_diversity_budget",
                "bias_multi_evaluation_selection",
            ]
        )
    return {
        "attention_budget": attention_budget,
        "exploration_budget": exploration_budget,
        "mutation_budget": mutation_budget,
        "selection_budget": selection_budget,
        "selection_budget_units": selection_budget_units,
        "selection_weights": selection_weights,
        "runtime_slot_allocation": runtime_slot_allocation,
        "memory_pressure": memory_state,
        "mutation_opportunity": mutation_budget,
        "selection_probability": dict(selection_weights),
        "runtime_slots": runtime_slot_allocation["runtime_slots"],
        "policy_budget": policy_budget,
        "evaluation_budget": evaluation_budget,
        "domain_expansion_budget": domain_expansion_budget,
        "repair_budget": repair_budget,
        "diversity_allocation_budget": diversity_allocation_budget,
        "evaluation_diversity_budget": evaluation_diversity_budget,
        "budget_mix": budget_mix,
        "economy_balance_score": economy_balance_score,
        "budget_skew": budget_skew,
        "rebalancing_actions": rebalancing_actions[:8],
        "budget_exhausted": budget_exhausted,
        "budget_remaining": max(0, exploration_budget - 1),
        "observable": True,
        "budget": exploration_budget,
    }


def exploration_economy(state: Mapping[str, Any]) -> dict[str, Any]:
    civilization_frame = dict(state.get("civilization_state", {})) if isinstance(state.get("civilization_state"), Mapping) else build_civilization_state(state=state)
    allocation = allocate_resources(
        dict(state.get("pressure", {})) if isinstance(state.get("pressure"), Mapping) else {},
        dict(state.get("ecology", {})) if isinstance(state.get("ecology"), Mapping) else {},
        dict(state.get("population", {})) if isinstance(state.get("population"), Mapping) else {},
        dict(state.get("manager_state", {})) if isinstance(state.get("manager_state"), Mapping) else None,
        dict(state.get("memory_pressure", {})) if isinstance(state.get("memory_pressure"), Mapping) else None,
        civilization_frame,
    )
    return {
        "attention_budget": allocation["attention_budget"],
        "mutation_budget": allocation["mutation_budget"],
        "selection_weights": allocation["selection_weights"],
        "runtime_slot_allocation": allocation["runtime_slot_allocation"],
        "memory_pressure": allocation["memory_pressure"],
    }


def economy_status(state: Mapping[str, Any]) -> dict[str, Any]:
    civilization_frame = dict(state.get("civilization_state", {})) if isinstance(state.get("civilization_state"), Mapping) else build_civilization_state(state=state)
    allocation = allocate_resources(
        dict(state.get("pressure", {})) if isinstance(state.get("pressure"), Mapping) else {},
        dict(state.get("ecology", {})) if isinstance(state.get("ecology"), Mapping) else {},
        dict(state.get("population", {})) if isinstance(state.get("population"), Mapping) else {},
        dict(state.get("manager_state", {})) if isinstance(state.get("manager_state"), Mapping) else None,
        dict(state.get("memory_pressure", {})) if isinstance(state.get("memory_pressure"), Mapping) else None,
        civilization_frame,
    )
    return {
        "attention_budget": allocation["attention_budget"],
        "exploration_budget": allocation["exploration_budget"],
        "mutation_budget": allocation["mutation_budget"],
        "selection_budget": allocation["selection_budget"],
        "runtime_slots": allocation["runtime_slots"],
        "policy_budget": allocation["policy_budget"],
        "evaluation_budget": allocation["evaluation_budget"],
        "selection_weights": allocation["selection_weights"],
        "selection_probability": allocation["selection_probability"],
        "domain_expansion_budget": allocation["domain_expansion_budget"],
        "repair_budget": allocation["repair_budget"],
        "diversity_allocation_budget": allocation["diversity_allocation_budget"],
        "evaluation_diversity_budget": allocation["evaluation_diversity_budget"],
        "budget_mix": allocation["budget_mix"],
        "economy_balance_score": allocation["economy_balance_score"],
        "budget_skew": allocation["budget_skew"],
        "rebalancing_actions": allocation["rebalancing_actions"],
        "budget_exhausted": allocation["budget_exhausted"],
        "budget_remaining": allocation["budget_remaining"],
        "runtime_slot_allocation": allocation["runtime_slot_allocation"],
        "memory_pressure": allocation["memory_pressure"],
        "observable": allocation["observable"],
    }


__all__ = ["allocate_resources", "economy_status", "exploration_economy"]
