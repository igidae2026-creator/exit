from __future__ import annotations

from typing import Any, Mapping

from domains.domain_genome import DomainGenome
from runtime.civilization_state import update_civilization_state
from runtime.orchestration.archive_stage import persist_runtime_frames
from runtime.orchestration.civilization_stage import build_civilization_frame
from runtime.orchestration.domain_routing_stage import build_routing_frame, evolve_domain_genome
from runtime.orchestration.economy_stage import build_economy_frame
from runtime.lineage_branching import lineage_branching
from runtime.orchestration.mutation_stage import apply_evaluation_mutation, apply_strategy_mutation, build_mutation_frame
from runtime.orchestration.pressure_stage import build_pressure_frame
from runtime.orchestration.recovery_stage import soften_worker_budget, validate_step_state
from runtime.orchestration.selection_stage import build_selection_frame


def step(
    metrics: Mapping[str, float],
    policy: Mapping[str, Any] | None,
    workers: int,
    *,
    domain: str,
    parent: str | None,
    genome: DomainGenome | None,
    deps: Mapping[str, Any],
) -> dict[str, Any]:
    deps["ensure_seed_domains"]()
    history = deps["metrics_tail"](40)
    pressure = build_pressure_frame(
        metrics,
        domain=domain,
        history=history,
        plateau_fn=deps["plateau"],
        novelty_drop_fn=deps["novelty_drop"],
        concentration_fn=deps["concentration"],
    )
    civilization_state = update_civilization_state(
        pressure.get("civilization_state", {}),
        {"pressure_state": dict(pressure["stabilized_pressure"])},
    )
    previous_market = history[-1].get("stabilized_market") if history and isinstance(history[-1].get("stabilized_market"), Mapping) else history[-1].get("market", {}) if history else {}
    stabilized_market = deps["stabilize_market"](pressure["market"], previous=previous_market, guard=pressure["guard"])
    mutation = build_mutation_frame(policy, pressure["stabilized_pressure"], stabilized_market, pressure["cooldown_state"])
    ecology = deps["evaluation_ecology"](history + [{"pressure": pressure["stabilized_pressure"], "quest": {"type": "work"}, **dict(metrics)}])
    evaluation_rows = deps["load_evaluations"]()
    evaluation_frame = deps["evolve_evaluation"](
        current=evaluation_rows[-1]["evaluation"] if evaluation_rows else None,
        pressure=pressure["stabilized_pressure"],
        market_state={
            **dict(stabilized_market),
            "policy_stagnation": float(civilization_state.get("policy_stagnation", 0.0)),
            "effective_lineage_diversity": float(civilization_state.get("effective_lineage_diversity", 0.0)),
            "domain_activation_rate": float(civilization_state.get("domain_activation_rate", 0.0)),
            "active_evaluation_generations": int(civilization_state.get("active_evaluation_generations", 0)),
            "evaluation_dominance_index": float(civilization_state.get("evaluation_dominance_index", 0.0)),
        },
    )
    evaluation = dict(evaluation_frame.get("evaluation", {})) if isinstance(evaluation_frame, Mapping) and isinstance(evaluation_frame.get("evaluation"), Mapping) else dict(evaluation_frame)
    strategy_rows = deps["load_exploration_strategies"]()
    exploration_strategy = deps["evolve_strategy"](current=strategy_rows[-1]["strategy"] if strategy_rows else None, pressure=pressure["stabilized_pressure"], market_state=stabilized_market)
    sos_rows = deps["load_strategy_of_strategy"]()
    strategy_of_strategy = deps["evolve_strategy_of_strategy"](current=sos_rows[-1]["strategy_of_strategy"] if sos_rows else None, pressure=pressure["stabilized_pressure"], market=stabilized_market, ecology=ecology)
    population = deps["artifact_population"](history)
    governance = deps["civilization_governor"](history, ecology, stabilized_market)
    meta = deps["meta_exploration"](history, ecology, population)
    strategy_of_strategy = apply_strategy_mutation(strategy_of_strategy, meta.get("strategy_mutation", {}) if isinstance(meta.get("strategy_mutation"), Mapping) else {})
    evaluation = apply_evaluation_mutation(evaluation, meta.get("evaluation_mutation", {}) if isinstance(meta.get("evaluation_mutation"), Mapping) else {})
    civilization = build_civilization_frame(history, population, ecology)
    civilization_state = update_civilization_state(
        civilization_state,
        civilization["civilization_state"],
    )
    if isinstance(meta.get("domain_creation"), Mapping) and meta["domain_creation"]:
        created_domain = deps["register_domain"](str(meta["domain_creation"].get("name", "meta_domain")), meta["domain_creation"])
        meta["domain_creation"] = dict(created_domain)
    if pressure["guard"]["reset_mutation_bias"]:
        stabilized_market["mutation_bias"] = round(min(float(stabilized_market.get("mutation_bias", 0.0)), 0.2), 6)
        mutation["policy_stack"]["mutation"]["rate"] = min(float(mutation["policy_stack"]["mutation"]["rate"]), 0.18)
    quota = deps["quota_frame"](pressure["stabilized_pressure"], workers, stabilized_market, tick=len(history) + 1, guard=pressure["guard"], history=history)
    budgets = deps["recover_budgets"](dict(quota.budgets), pressure["guard"], history=history)
    economy = build_economy_frame(
        pressure["stabilized_pressure"],
        ecology,
        population,
        civilization["memory_state"],
        budgets,
        civilization_state=civilization_state,
    )
    civilization_state = update_civilization_state(
        civilization_state,
        {
            "exploration_budget": int(economy["budgets"].get("exploration_budget", 0)),
            "pressure_state": dict(pressure["stabilized_pressure"]),
        },
    )
    selection = build_selection_frame(
        pressure["stabilized_pressure"],
        {
            **dict(stabilized_market),
            "active_evaluation_generations": int(civilization_state.get("active_evaluation_generations", 0)),
            "evaluation_dominance_index": float(civilization_state.get("evaluation_dominance_index", 0.0)),
            "evaluation_diversity": float(civilization_state.get("evaluation_diversity", 0.0)),
        },
        ecology,
        population,
        governance,
        tick=len(history) + 1,
    )
    active_meta_quest = deps["meta_quest"](pressure["stabilized_pressure"], recent_state=pressure["recent_state"])
    if pressure["guard"]["force_meta"] and active_meta_quest is None and not pressure["cooldown_state"]["meta_locked"] and pressure["cooldown_state"]["preferred_type"] != "exploration":
        active_meta_quest = {"type": "meta", "priority": "high", "reasons": ["collapse_guard"], "quest_types": ["meta", "reframing", "repair"], "pressure": {key: round(float(value), 4) for key, value in pressure["stabilized_pressure"].items()}, "cooldown": pressure["cooldown_state"]}
    slots = deps["quest_slots"](pressure["stabilized_pressure"], recent_state=pressure["recent_state"], plateau_hit=pressure["plateau_hit"], lineage_high=pressure["lineage_high"], novelty_low_sustained=pressure["novelty_low_sustained"])
    quest = deps["active_quest"](slots)
    if active_meta_quest is not None:
        quest = dict(active_meta_quest)
    elif pressure["cooldown_state"]["preferred_type"] == "exploration" and quest.get("type") in {"meta", "repair"}:
        quest = {"type": "exploration", "mode": "stabilize", "priority": "high", "cooldown": pressure["cooldown_state"]}
    elif pressure["cooldown_state"]["preferred_type"] == "work" and quest.get("type") == "repair":
        quest = {"type": "work", "priority": "normal", "cooldown": pressure["cooldown_state"]}
    elif pressure["guard"]["force_reframing"] and quest.get("type") not in {"repair", "meta"}:
        quest = {"type": "exploration", "mode": "stabilize", "priority": "high", "cooldown": pressure["cooldown_state"]} if pressure["cooldown_state"]["reframing_locked"] else {"type": "reframing", "priority": "high", "reason": "collapse_guard", "cooldown": pressure["cooldown_state"]}
    quest = deps["rebalance_quest"](quest, pressure["stabilized_pressure"], pressure["recent_state"], pressure["cooldown_state"], pressure["guard"])
    if pressure["plateau_hit"] and quest.get("type") not in {"repair", "meta"}:
        quest = {"type": "reframing", "priority": "high", "reason": "plateau", "cooldown": pressure["cooldown_state"]}
    if quest.get("type") == "reframing":
        active_meta_quest = None
    new_policy = deps["evolve_policy"](mutation["flat_policy"], pressure["stabilized_pressure"])
    policy_artifact_id = deps["register_policy_artifact"](new_policy, pressure["stabilized_pressure"], float(metrics.get("score", 0.0)), parent=parent)
    policy_stack_artifact_id = deps["register_policy_stack_artifact"](mutation["policy_stack"], parent=parent, score=float(metrics.get("score", 0.0)))
    evaluation_artifact_id = deps["register_evaluation_artifact"](evaluation, pressure["stabilized_pressure"], float(metrics.get("score", 0.0)), parent=parent)
    exploration_strategy_artifact_id = deps["register_exploration_strategy_artifact"](exploration_strategy, pressure["stabilized_pressure"], stabilized_market, float(metrics.get("score", 0.0)), parent=parent)
    strategy_of_strategy_artifact_id = deps["register_strategy_of_strategy_artifact"](strategy_of_strategy, pressure["stabilized_pressure"], stabilized_market, ecology, float(metrics.get("score", 0.0)), parent=parent)
    civilization_selection_artifact_id = deps["register_civilization_selection_artifact"](selection["civilization_selection"], parent=parent, score=float(metrics.get("score", 0.0)))
    repair = deps["emit_repair_artifact"](metrics, pressure["stabilized_pressure"], parent=parent)
    if pressure["guard"]["freeze_export"] and repair is None:
        repair = {"artifact_id": None, "type": "export_freeze"}
    if repair and pressure["recent_state"].get("repair_cycle_streak", 0) >= 2:
        quest = {"type": "repair", "priority": "high", "escalation": "repair_failure", "cooldown": pressure["cooldown_state"]}
    budgets = soften_worker_budget(economy["budgets"], pressure["stabilized_pressure"], pressure["guard"], quest, repair)
    cycle_transition = deps["exploration_cycle"](history, int(budgets.get("exploration_budget", 2)), quest)
    budgets["exploration_depth"] = cycle_transition["depth"]
    if cycle_transition["exhausted"]:
        quest = {"type": "reframing", "priority": "high", "reason": "exploration_budget_exhausted", "cooldown": pressure["cooldown_state"], "exploration_cycle": dict(cycle_transition)}
    routing = build_routing_frame(pressure["stabilized_pressure"], budgets, domain=domain, guard=pressure["guard"], ecology=ecology, civilization_selection=selection["civilization_selection"], history=history)
    lineage_frame = lineage_branching(
        history,
        pressure["stabilized_pressure"],
        domain=str(routing["routing"].get("selected_domain", domain)),
        tick=len(history) + 1,
        evaluation_generations=int(evaluation_frame.get("evaluation_generation_count", 0)) if isinstance(evaluation_frame, Mapping) else 0,
        policy_stagnation=float(civilization_state.get("policy_stagnation", 0.0)),
    )
    routing["routing"]["selected_lineage"] = str(lineage_frame.get("selected_lineage", routing["routing"].get("selected_domain", domain)))
    allocator_artifact_id = deps["register_allocator_artifact"]({"market": stabilized_market}, pressure["stabilized_pressure"], int(budgets["effective_workers"]), budgets, parent=parent)
    domain_frame = evolve_domain_genome(pressure["stabilized_pressure"], domain=domain, genome=genome, active_meta_quest=active_meta_quest, routing=routing["routing"], ecology=ecology)
    crossbred_domain_artifact_id = None
    if domain_frame["crossbred_genome"] is not None:
        crossbred_domain_artifact_id = deps["register_crossbred_domain_artifact"]({"genome": domain_frame["crossbred_genome"], "selected_domain": str(routing["routing"].get("selected_domain", domain))}, parent=parent, score=float(metrics.get("score", 0.0)), novelty=float(metrics.get("novelty", 0.0)), diversity=float(metrics.get("diversity", 0.0)), cost=float(metrics.get("cost", 0.0)))
    domain_artifact_id = deps["register_domain_artifact"]({"genome": domain_frame["genome"], "routing": routing["routing"]}, parent=parent, score=float(metrics.get("score", 0.0)), novelty=float(metrics.get("novelty", 0.0)), diversity=float(metrics.get("diversity", 0.0)), cost=float(metrics.get("cost", 0.0)))
    artifact_id = deps["register_quest_artifact"]({"pressure": pressure["stabilized_pressure"], "workers": int(budgets["effective_workers"]), "genome": domain_frame["genome"], "budgets": budgets, "routing": routing["routing"]}, parent=parent, score=float(metrics.get("score", 0.0)), novelty=float(metrics.get("novelty", 0.0)), diversity=float(metrics.get("diversity", 0.0)), cost=float(metrics.get("cost", 0.0)), quest=quest, policy=new_policy)
    result = {
        "artifact_id": artifact_id,
        "quest": quest,
        "meta_quest": active_meta_quest,
        "policy": new_policy,
        "policy_stack": mutation["policy_stack"],
        "policy_artifact_id": policy_artifact_id,
        "policy_stack_artifact_id": policy_stack_artifact_id,
        "evaluation_artifact_id": evaluation_artifact_id,
        "exploration_strategy_artifact_id": exploration_strategy_artifact_id,
        "strategy_of_strategy_artifact_id": strategy_of_strategy_artifact_id,
        "allocator_artifact_id": allocator_artifact_id,
        "domain_artifact_id": domain_artifact_id,
        "evaluation": evaluation,
        "evaluation_generation_count": int(evaluation_frame.get("evaluation_generation_count", 0)) if isinstance(evaluation_frame, Mapping) else 0,
        "evaluation_turnover": float(evaluation_frame.get("evaluation_turnover", 0.0)) if isinstance(evaluation_frame, Mapping) else 0.0,
        "active_evaluation_generations": int(evaluation_frame.get("active_evaluation_generations", 0)) if isinstance(evaluation_frame, Mapping) else 0,
        "dormant_evaluation_generations": int(evaluation_frame.get("dormant_evaluation_generations", 0)) if isinstance(evaluation_frame, Mapping) else 0,
        "retired_evaluation_generations": int(evaluation_frame.get("retired_evaluation_generations", 0)) if isinstance(evaluation_frame, Mapping) else 0,
        "evaluation_branch_rate": float(evaluation_frame.get("evaluation_branch_rate", 0.0)) if isinstance(evaluation_frame, Mapping) else 0.0,
        "evaluation_diversity": float(evaluation_frame.get("evaluation_diversity", 0.0)) if isinstance(evaluation_frame, Mapping) else 0.0,
        "evaluation_dominance_index": float(evaluation_frame.get("evaluation_dominance_index", 0.0)) if isinstance(evaluation_frame, Mapping) else 0.0,
        "evaluation_retirement_rate": float(evaluation_frame.get("evaluation_retirement_rate", 0.0)) if isinstance(evaluation_frame, Mapping) else 0.0,
        "evaluation_reactivation_rate": float(evaluation_frame.get("evaluation_reactivation_rate", 0.0)) if isinstance(evaluation_frame, Mapping) else 0.0,
        "active_evaluation_distribution": dict(evaluation_frame.get("active_evaluation_distribution", {})) if isinstance(evaluation_frame, Mapping) else {},
        "ecology": ecology,
        "exploration_strategy": exploration_strategy,
        "strategy_of_strategy": strategy_of_strategy,
        "civilization_selection": selection["civilization_selection"],
        "population": population,
        "governance": governance,
        "economy": economy["economy"],
        "exploration_economy_state": economy["economy"],
        "resource_allocation": economy["resource_allocation"],
        "civilization_state": civilization_state,
        "civilization_stability": civilization["civilization_stability"],
        "exploration_cycle": cycle_transition,
        "meta_exploration": meta,
        "guard": pressure["guard"],
        "cooldown": pressure["cooldown_state"],
        "repair": repair,
        "workers": int(budgets["effective_workers"]),
        "pressure": pressure["pressure"],
        "stabilized_pressure": pressure["stabilized_pressure"],
        "market": stabilized_market,
        "stabilized_market": stabilized_market,
        "budgets": budgets,
        "routing": routing["routing"],
        "lineage": lineage_frame,
        "domain": domain,
        "genome": domain_frame["genome"],
    }
    validate_step_state(result)
    persist_runtime_frames(
        deps["save"],
        deps["remember"],
        {
            **result,
            "policy_stack": mutation["policy_stack"],
            "economy": economy["economy"],
            "exploration_economy_state": economy["economy"],
        },
    )
    deps["remember"]("quest_artifact", {"artifact_id": artifact_id, "quest": quest})
    deps["remember"]("policy_artifact", {"artifact_id": policy_artifact_id, "policy": new_policy})
    deps["remember"]("policy_stack_artifact", {"artifact_id": policy_stack_artifact_id, "policy_stack": mutation["policy_stack"]})
    deps["remember"]("evaluation_artifact", {"artifact_id": evaluation_artifact_id, "evaluation": evaluation})
    deps["remember"]("exploration_strategy_artifact", {"artifact_id": exploration_strategy_artifact_id, "strategy": exploration_strategy})
    deps["remember"]("strategy_of_strategy_artifact", {"artifact_id": strategy_of_strategy_artifact_id, "strategy_of_strategy": strategy_of_strategy})
    deps["remember"]("civilization_selection_artifact", {"artifact_id": civilization_selection_artifact_id, "selection": selection["civilization_selection"]})
    deps["remember"]("allocator_artifact", {"artifact_id": allocator_artifact_id, "budgets": budgets})
    deps["remember"]("domain_genome_snapshot", {"artifact_id": domain_artifact_id, "genome": domain_frame["genome"], "routing": routing["routing"]})
    if crossbred_domain_artifact_id:
        deps["remember"]("crossbred_domain_artifact", {"artifact_id": crossbred_domain_artifact_id, "genome": domain_frame["genome"]})
    return result


__all__ = ["step"]
