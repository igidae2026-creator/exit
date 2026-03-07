from __future__ import annotations

from typing import Any, Mapping

from artifact.archive import save
from metaos.observer.metrics_history import novelty_drop, plateau
from metaos.observer.metrics_history import tail as metrics_tail
from metaos.policy.evaluation_artifact import load_all as load_evaluations
from runtime.civilization_memory import remember
from runtime.evaluation_evolution import evolve_evaluations as evolve_evaluation
from metaos.policy.evolve_policy import evolve as evolve_policy
from metaos.registry.lineage_graph import concentration
from runtime.orchestration.pipeline import step as _step
from runtime.artifact_civilization import (
    register_allocator_artifact,
    register_civilization_selection_artifact,
    register_crossbred_domain_artifact,
    register_domain_artifact,
    register_evaluation_artifact,
    register_exploration_strategy_artifact,
    register_policy_artifact,
    register_policy_stack_artifact,
    register_quest_artifact,
    register_strategy_of_strategy_artifact,
)
from runtime.artifact_population import artifact_population
from runtime.civilization_governor import civilization_governor
from runtime.domain_pool import ensure_seed_domains, get_domain, register_domain
from runtime.evaluation_ecology import evaluation_ecology
from runtime.evolve_exploration_strategy import evolve_strategy
from runtime.exploration_market_stability import stabilize_market
from runtime.exploration_strategy_artifact import load_all as load_exploration_strategies
from runtime.meta_exploration import meta_exploration
from runtime.meta_quest_engine import meta_quest
from runtime.recovery_allocator import recover_budgets
from runtime.repair_system import emit_repair_artifact
from runtime.strategy_of_strategy import evolve_strategy_of_strategy, load_all as load_strategy_of_strategy
from runtime.exploration_cycle import exploration_cycle
from strategy.quota import quota_frame
from strategy.quest_portfolio import active_quest, quest_slots


def rebalance_quest(
    quest: Mapping[str, Any],
    pressure: Mapping[str, float],
    recent_state: Mapping[str, Any],
    cooldown_state: Mapping[str, Any],
    guard: Mapping[str, Any],
) -> dict[str, Any]:
    q = dict(quest)
    qtype = str(q.get("type", "work"))
    novelty_persist = bool(recent_state.get("novelty_collapse_persist")) or float(pressure.get("novelty_pressure", 0.0)) >= 0.95
    lineage_collapse = int(recent_state.get("lineage_high_streak", 0)) >= 3 or float(pressure.get("diversity_pressure", 0.0)) >= 0.85
    meta_share = float(recent_state.get("meta_share", 0.0) or 0.0)
    reframing_share = float(recent_state.get("reframing_share", 0.0) or 0.0)
    work_exploration_share = float(recent_state.get("work_exploration_share", 0.0) or 0.0)
    meta_locked = bool(cooldown_state.get("meta_locked"))
    if bool(cooldown_state.get("force_exploration")):
        return {"type": "exploration", "mode": "stabilize", "priority": "high", "cooldown": dict(cooldown_state)}
    if meta_locked and qtype == "meta":
        return {"type": "exploration", "mode": "stabilize", "priority": "high", "cooldown": dict(cooldown_state)}
    if novelty_persist and not lineage_collapse and not bool(cooldown_state.get("reframing_locked")) and reframing_share < 0.12 and qtype in {"meta", "exploration", "work"}:
        return {"type": "reframing", "priority": "high", "reason": "distribution_balance", "cooldown": dict(cooldown_state)}
    if meta_share > 0.30 and qtype == "meta":
        return {"type": "exploration", "mode": "stabilize", "priority": "high", "cooldown": dict(cooldown_state)}
    if work_exploration_share < 0.50 and qtype in {"meta", "reframing"} and not bool(guard.get("freeze_export")):
        return {"type": "exploration", "mode": "stabilize", "priority": "high", "cooldown": dict(cooldown_state)}
    if novelty_persist and not bool(cooldown_state.get("reframing_locked")) and reframing_share < 0.05 and qtype in {"work", "exploration"}:
        return {"type": "reframing", "priority": "high", "reason": "distribution_balance", "cooldown": dict(cooldown_state)}
    if qtype == "repair" and cooldown_state.get("preferred_type") == "work":
        return {"type": "work", "priority": "normal", "cooldown": dict(cooldown_state)}
    return q


def step(
    metrics: Mapping[str, float],
    policy: Mapping[str, Any] | None,
    workers: int,
    domain: str = "default",
    parent: str | None = None,
    genome: Any | None = None,
) -> dict[str, Any]:
    return _step(
        metrics,
        policy,
        workers,
        domain=domain,
        parent=parent,
        genome=genome,
        deps={
            "active_quest": active_quest,
            "artifact_population": artifact_population,
            "civilization_governor": civilization_governor,
            "concentration": concentration,
            "emit_repair_artifact": emit_repair_artifact,
            "ensure_seed_domains": ensure_seed_domains,
            "evaluation_ecology": evaluation_ecology,
            "evolve_evaluation": evolve_evaluation,
            "evolve_exploration_strategy": evolve_strategy,
            "evolve_policy": evolve_policy,
            "evolve_strategy": evolve_strategy,
            "evolve_strategy_of_strategy": evolve_strategy_of_strategy,
            "exploration_cycle": exploration_cycle,
            "load_evaluations": load_evaluations,
            "load_exploration_strategies": load_exploration_strategies,
            "load_strategy_of_strategy": load_strategy_of_strategy,
            "meta_exploration": meta_exploration,
            "meta_quest": meta_quest,
            "metrics_tail": metrics_tail,
            "novelty_drop": novelty_drop,
            "plateau": plateau,
            "quota_frame": quota_frame,
            "rebalance_quest": rebalance_quest,
            "recover_budgets": recover_budgets,
            "register_allocator_artifact": register_allocator_artifact,
            "register_civilization_selection_artifact": register_civilization_selection_artifact,
            "register_crossbred_domain_artifact": register_crossbred_domain_artifact,
            "register_domain": register_domain,
            "register_domain_artifact": register_domain_artifact,
            "register_evaluation_artifact": register_evaluation_artifact,
            "register_exploration_strategy_artifact": register_exploration_strategy_artifact,
            "register_policy_artifact": register_policy_artifact,
            "register_policy_stack_artifact": register_policy_stack_artifact,
            "register_quest_artifact": register_quest_artifact,
            "register_strategy_of_strategy_artifact": register_strategy_of_strategy_artifact,
            "remember": remember,
            "save": save,
            "stabilize_market": stabilize_market,
            "quest_slots": quest_slots,
        },
    )


__all__ = [
    "active_quest",
    "concentration",
    "ensure_seed_domains",
    "get_domain",
    "load_evaluations",
    "load_exploration_strategies",
    "load_strategy_of_strategy",
    "metrics_tail",
    "novelty_drop",
    "plateau",
    "rebalance_quest",
    "register_domain",
    "remember",
    "save",
    "step",
]
