from __future__ import annotations

import copy
import math
from typing import Any, Mapping

from metaos.archive.archive import save
from metaos.archive.civilization_memory import remember
from metaos.domains.domain_genome import DomainGenome
from metaos.domains.domain_genome_mutation import mutate_domain_genome
from metaos.domains.domain_recombination import recombine
from metaos.observer.metrics_history import novelty_drop, plateau
from metaos.observer.metrics_history import tail as metrics_tail
from metaos.observer.pressure_engine import pressure
from metaos.policy.evaluation_artifact import load_all as load_evaluations
from metaos.policy.evolve_evaluation import evolve_evaluation
from metaos.policy.evolve_policy import evolve
from metaos.policy.policy_stack import default_policy_stack, evolve_policy_stack
from metaos.runtime.artifact_civilization import (
    register_allocator_artifact,
    register_domain_artifact,
    register_evaluation_artifact,
    register_exploration_strategy_artifact,
    register_policy_artifact,
    register_policy_stack_artifact,
    register_quest_artifact,
)
from metaos.runtime.collapse_guard import detect_guard_state
from metaos.runtime.domain_router import route
from metaos.runtime.evolve_exploration_strategy import evolve_strategy
from metaos.runtime.exploration_market_stability import stabilize_market
from metaos.runtime.exploration_strategy_artifact import load_all as load_exploration_strategies
from metaos.runtime.meta_cooldown import quest_cooldown
from metaos.runtime.meta_quest_engine import meta_quest
from metaos.runtime.pressure_market import market
from metaos.runtime.pressure_ecology import stabilize_pressure
from metaos.runtime.recovery_allocator import recover_budgets
from metaos.registry.lineage_graph import concentration
from metaos.runtime.quota_allocator import allocate
from metaos.runtime.repair_system import emit_repair_artifact
from metaos.runtime.quest_system import spawn_quest


def _normalize_stack(policy: Mapping[str, Any] | None) -> dict[str, dict[str, float]]:
    defaults = default_policy_stack()
    if not policy:
        return defaults
    if all(key in policy for key in defaults):
        out = copy.deepcopy(defaults)
        for section in defaults:
            incoming = policy.get(section, {})
            if isinstance(incoming, Mapping):
                out[section].update({key: round(float(value), 4) for key, value in incoming.items() if key in out[section]})
        return out
    out = copy.deepcopy(defaults)
    out["selection"].update(
        {
            "score": round(float(policy.get("selection_weight_score", out["selection"]["score"])), 4),
            "novelty": round(float(policy.get("selection_weight_novelty", out["selection"]["novelty"])), 4),
            "diversity": round(float(policy.get("selection_weight_diversity", out["selection"]["diversity"])), 4),
            "efficiency": round(float(policy.get("selection_weight_efficiency", out["selection"]["efficiency"])), 4),
        }
    )
    out["mutation"]["rate"] = round(float(policy.get("mutation_rate", out["mutation"]["rate"])), 4)
    out["selection"]["share_threshold"] = round(float(policy.get("share_threshold", 0.75)), 4)
    return out


def _flat_policy(stack: Mapping[str, Mapping[str, float]]) -> dict[str, float]:
    selection = dict(stack.get("selection", {}))
    mutation = dict(stack.get("mutation", {}))
    return {
        "selection_weight_score": round(float(selection.get("score", 0.42)), 4),
        "selection_weight_novelty": round(float(selection.get("novelty", 0.23)), 4),
        "selection_weight_diversity": round(float(selection.get("diversity", 0.2)), 4),
        "selection_weight_efficiency": round(float(selection.get("efficiency", 0.15)), 4),
        "mutation_rate": round(float(mutation.get("rate", 0.2)), 4),
        "share_threshold": round(float(selection.get("share_threshold", 0.75)), 4),
    }


def _recent_state(guard_history: list[dict[str, Any]]) -> dict[str, int]:
    history = guard_history[-8:]
    rolling = guard_history[-32:]
    plateau_streak = sum(1 for row in history if float(row.get("domain_shift_pressure", row.get("pressure", {}).get("domain_shift_pressure", 0.0))) >= 0.7)
    novelty_low_streak = sum(1 for row in history if float(row.get("novelty", 1.0)) <= 0.25)
    lineage_high_streak = sum(1 for row in history if float(row.get("lineage_pressure", row.get("pressure", {}).get("lineage_pressure", 0.0))) >= 0.6)
    repair_cycle_streak = sum(1 for row in history if row.get("repair"))
    domains = [str(row.get("routing", {}).get("selected_domain", row.get("domain", "default"))) for row in history]
    routing_stagnation = len(history) if history and len(set(domains)) <= 1 else 0
    meta_repeat = 0
    reframing_repeat = 0
    repair_repeat = 0
    for row in reversed(history):
        quest = row.get("quest", {}) if isinstance(row.get("quest"), Mapping) else {}
        qtype = str(quest.get("type", ""))
        if not qtype:
            continue
        if qtype == "meta":
            meta_repeat += 1
        else:
            break
    for row in reversed(history):
        quest = row.get("quest", {}) if isinstance(row.get("quest"), Mapping) else {}
        qtype = str(quest.get("type", ""))
        if not qtype:
            continue
        if qtype == "reframing":
            reframing_repeat += 1
        else:
            break
    for row in reversed(history):
        quest = row.get("quest", {}) if isinstance(row.get("quest"), Mapping) else {}
        repair = row.get("repair")
        qtype = str(quest.get("type", ""))
        if not qtype and not repair:
            continue
        if qtype == "repair" or repair:
            repair_repeat += 1
        else:
            break
    guard_active = any(bool((row.get("guard", {}) if isinstance(row.get("guard"), Mapping) else {}).get(flag)) for row in history for flag in ("freeze_export", "downshift_workers", "force_reframing", "force_meta"))
    rolling_quests = [str((row.get("quest", {}) if isinstance(row.get("quest"), Mapping) else {}).get("type", "")) for row in rolling]
    rolling_quests = [qtype for qtype in rolling_quests if qtype]
    total = len(rolling_quests) or 1
    meta_share = sum(1 for qtype in rolling_quests if qtype == "meta") / total
    reframing_share = sum(1 for qtype in rolling_quests if qtype == "reframing") / total
    work_exploration_share = sum(1 for qtype in rolling_quests if qtype in {"work", "exploration"}) / total
    failed_reframing_repeat = 0
    for row in reversed(history):
        quest = row.get("quest", {}) if isinstance(row.get("quest"), Mapping) else {}
        qtype = str(quest.get("type", ""))
        pressure_row = row.get("pressure", {}) if isinstance(row.get("pressure"), Mapping) else {}
        if qtype != "reframing":
            break
        if (
            float(row.get("novelty", 1.0)) <= 0.25
            or float(pressure_row.get("novelty_pressure", 0.0)) >= 0.85
            or float(pressure_row.get("domain_shift_pressure", 0.0)) >= 0.45
        ):
            failed_reframing_repeat += 1
        else:
            break
    novelty_collapse_persist = (
        sum(1 for row in rolling if float(row.get("novelty", 1.0)) <= 0.25) >= max(3, math.ceil(len(rolling) * 0.25))
        if rolling
        else False
    )
    return {
        "plateau_streak": plateau_streak,
        "novelty_low_streak": novelty_low_streak,
        "lineage_high_streak": lineage_high_streak,
        "repair_cycle_streak": repair_cycle_streak,
        "routing_stagnation": routing_stagnation,
        "meta_repeat": meta_repeat,
        "reframing_repeat": reframing_repeat,
        "repair_repeat": repair_repeat,
        "guard_active": int(guard_active),
        "failed_reframing_repeat": failed_reframing_repeat,
        "meta_share": round(meta_share, 4),
        "reframing_share": round(reframing_share, 4),
        "work_exploration_share": round(work_exploration_share, 4),
        "novelty_collapse_persist": int(novelty_collapse_persist),
    }


def _quest_with_type(qtype: str, cooldown_state: Mapping[str, Any]) -> dict[str, Any]:
    if qtype == "exploration":
        return {"type": "exploration", "mode": "stabilize", "priority": "high", "cooldown": dict(cooldown_state)}
    if qtype == "reframing":
        return {"type": "reframing", "priority": "high", "reason": "distribution_balance", "cooldown": dict(cooldown_state)}
    if qtype == "work":
        return {"type": "work", "priority": "normal", "cooldown": dict(cooldown_state)}
    return {"type": qtype, "priority": "high", "cooldown": dict(cooldown_state)}


def _rebalance_quest(
    quest: Mapping[str, Any],
    pressure: Mapping[str, float],
    recent_state: Mapping[str, Any],
    cooldown_state: Mapping[str, Any],
    guard: Mapping[str, Any],
) -> dict[str, Any]:
    q = dict(quest)
    qtype = str(q.get("type", "work"))
    novelty_persist = bool(recent_state.get("novelty_collapse_persist")) or float(pressure.get("novelty_pressure", 0.0)) >= 0.95
    lineage_collapse = int(recent_state.get("lineage_high_streak", 0)) >= 3 or float(pressure.get("lineage_pressure", 0.0)) >= 0.75
    meta_share = float(recent_state.get("meta_share", 0.0) or 0.0)
    reframing_share = float(recent_state.get("reframing_share", 0.0) or 0.0)
    work_exploration_share = float(recent_state.get("work_exploration_share", 0.0) or 0.0)
    meta_locked = bool(cooldown_state.get("meta_locked"))
    fallback_order = ["exploration", "reframing", "work"] if meta_locked else ["exploration", "work"]
    if bool(cooldown_state.get("force_exploration")):
        return _quest_with_type("exploration", cooldown_state)
    if meta_locked and qtype == "meta":
        for candidate in fallback_order:
            if candidate == "reframing" and (bool(cooldown_state.get("reframing_locked")) or not novelty_persist):
                continue
            return _quest_with_type(candidate, cooldown_state)
    if novelty_persist and not lineage_collapse and not bool(cooldown_state.get("reframing_locked")):
        if reframing_share < 0.12 and qtype in {"meta", "exploration", "work"}:
            return _quest_with_type("reframing", cooldown_state)
    if meta_share > 0.30 and qtype == "meta":
        return _quest_with_type("exploration", cooldown_state)
    if work_exploration_share < 0.50 and qtype in {"meta", "reframing"} and not bool(guard.get("freeze_export")):
        return _quest_with_type("exploration", cooldown_state)
    if novelty_persist and not bool(cooldown_state.get("reframing_locked")):
        if reframing_share < 0.05 and qtype in {"work", "exploration"}:
            return _quest_with_type("reframing", cooldown_state)
        if reframing_share > 0.20 and qtype == "reframing":
            return _quest_with_type("exploration", cooldown_state)
    if qtype == "repair" and cooldown_state.get("preferred_type") == "work":
        return _quest_with_type("work", cooldown_state)
    return q


def _soften_worker_budget(
    budgets: Mapping[str, float | int],
    pressure: Mapping[str, float],
    guard: Mapping[str, Any],
    quest: Mapping[str, Any],
    repair: Any,
) -> dict[str, float | int]:
    out = dict(budgets)
    effective_workers = int(out.get("effective_workers", out.get("workers", 0)))
    if effective_workers < 28:
        return out
    if repair or bool(guard.get("freeze_export")) or bool(guard.get("downshift_workers")):
        return out
    if str((quest or {}).get("type", "")) == "meta":
        return out
    combined_pressure = (
        float(pressure.get("novelty_pressure", 0.0))
        + float(pressure.get("diversity_pressure", 0.0))
        + float(pressure.get("domain_shift_pressure", 0.0))
    )
    if combined_pressure >= 2.15:
        return out
    reduced_workers = max(12, int(round(effective_workers * 0.93)))
    if reduced_workers >= effective_workers:
        reduced_workers = effective_workers - 1
    if reduced_workers < 12:
        return out
    scale = reduced_workers / max(1, effective_workers)
    for key in ("mutation_budget", "replay_budget", "repair_budget", "archive_budget", "domain_budget"):
        out[key] = round(float(out.get(key, 0.0)) * scale, 4)
    out["worker_budget"] = reduced_workers
    out["workers"] = reduced_workers
    out["effective_workers"] = reduced_workers
    return out


def step(
    metrics: Mapping[str, float],
    policy: Mapping[str, Any] | None,
    workers: int,
    domain: str = "default",
    parent: str | None = None,
    genome: DomainGenome | None = None,
) -> dict[str, Any]:
    raw_pressure = pressure(metrics)
    plateau_hit = plateau()
    lineage_high = concentration() > 0.45
    novelty_low_sustained = novelty_drop()
    history = metrics_tail(40)
    preliminary_guard = detect_guard_state(history + [{"pressure": raw_pressure, "domain": domain, **dict(metrics)}])
    stabilized_pressure = stabilize_pressure(raw_pressure, history=history, guard=preliminary_guard)
    raw_market = market(stabilized_pressure)
    previous_market = history[-1].get("stabilized_market") if history and isinstance(history[-1].get("stabilized_market"), Mapping) else history[-1].get("market", {}) if history else {}
    stabilized_market = stabilize_market(raw_market, previous=previous_market, guard=preliminary_guard)
    guard_seed = history + [{"pressure": stabilized_pressure, "stabilized_pressure": stabilized_pressure, "domain": domain, **dict(metrics)}]
    recent_state = _recent_state(guard_seed)
    guard = detect_guard_state(guard_seed)
    recent_state["guard_active"] = int(any(bool(guard.get(key)) for key in ("freeze_export", "downshift_workers", "force_reframing", "force_meta")))
    cooldown_state = quest_cooldown(recent_state)
    policy_stack = _normalize_stack(policy)
    policy_stack = evolve_policy_stack(policy_stack, stabilized_pressure, stabilized_market, cooldown_state=cooldown_state)
    flat_policy_seed = _flat_policy(policy_stack)
    evaluation_rows = load_evaluations()
    current_evaluation = evaluation_rows[-1]["evaluation"] if evaluation_rows else None
    evaluation = evolve_evaluation(current=current_evaluation, pressure=stabilized_pressure, market_state=stabilized_market)
    strategy_rows = load_exploration_strategies()
    current_strategy = strategy_rows[-1]["strategy"] if strategy_rows else None
    exploration_strategy = evolve_strategy(current=current_strategy, pressure=stabilized_pressure, market_state=stabilized_market)
    if guard["reset_mutation_bias"]:
        stabilized_market["mutation_bias"] = round(min(float(stabilized_market.get("mutation_bias", 0.0)), 0.2), 6)
        policy_stack["mutation"]["rate"] = min(float(policy_stack["mutation"]["rate"]), 0.18)
    budgets = allocate(stabilized_pressure, workers, market_state=stabilized_market, guard=guard, history=history)
    budgets = recover_budgets(budgets, guard, history=history)
    active_meta_quest = meta_quest(stabilized_pressure, recent_state=recent_state)
    if guard["force_meta"] and active_meta_quest is None and not cooldown_state["meta_locked"] and cooldown_state["preferred_type"] != "exploration":
        active_meta_quest = {
            "type": "meta",
            "priority": "high",
            "reasons": ["collapse_guard"],
            "quest_types": ["meta", "reframing", "repair"],
            "pressure": {key: round(float(value), 4) for key, value in stabilized_pressure.items()},
            "cooldown": cooldown_state,
        }
    q = spawn_quest(
        stabilized_pressure,
        plateau_hit=plateau_hit,
        lineage_high=lineage_high,
        novelty_low_sustained=novelty_low_sustained,
    )
    if active_meta_quest is not None:
        q = dict(active_meta_quest)
    elif cooldown_state["preferred_type"] == "exploration" and q.get("type") in {"meta", "repair"}:
        q = {"type": "exploration", "mode": "stabilize", "priority": "high", "cooldown": cooldown_state}
    elif cooldown_state["preferred_type"] == "work" and q.get("type") == "repair":
        q = {"type": "work", "priority": "normal", "cooldown": cooldown_state}
    elif guard["force_reframing"] and q.get("type") not in {"repair", "meta"}:
        if cooldown_state["reframing_locked"]:
            q = {"type": "exploration", "mode": "stabilize", "priority": "high", "cooldown": cooldown_state}
        else:
            q = {"type": "reframing", "priority": "high", "reason": "collapse_guard", "cooldown": cooldown_state}
    q = _rebalance_quest(q, stabilized_pressure, recent_state, cooldown_state, guard)
    if q.get("type") == "reframing":
        active_meta_quest = None
    new_policy = evolve(flat_policy_seed, stabilized_pressure)
    policy_artifact_id = register_policy_artifact(new_policy, stabilized_pressure, float(metrics.get("score", 0.0)), parent=parent)
    policy_stack_artifact_id = register_policy_stack_artifact(policy_stack, parent=parent, score=float(metrics.get("score", 0.0)))
    evaluation_artifact_id = register_evaluation_artifact(evaluation, stabilized_pressure, float(metrics.get("score", 0.0)), parent=parent)
    exploration_strategy_artifact_id = register_exploration_strategy_artifact(
        exploration_strategy,
        stabilized_pressure,
        stabilized_market,
        float(metrics.get("score", 0.0)),
        parent=parent,
    )
    repair = emit_repair_artifact(metrics, stabilized_pressure, parent=parent)
    if guard["freeze_export"] and repair is None:
        repair = {"artifact_id": None, "type": "export_freeze"}
    budgets = _soften_worker_budget(budgets, stabilized_pressure, guard, q, repair)
    routing = route(stabilized_pressure, budgets, domain=domain, guard=guard)
    if guard["force_reframing"]:
        routing["stagnation_escape"] = True
    new_workers = int(budgets["effective_workers"])
    allocator_artifact_id = register_allocator_artifact(
        {"market": stabilized_market},
        stabilized_pressure,
        new_workers,
        budgets,
        parent=parent,
    )
    active_genome = genome or DomainGenome(name=domain)
    genome_state = active_genome.as_dict()
    if (
        float(stabilized_pressure.get("domain_shift_pressure", 0.0)) > 0.70
        or float(stabilized_pressure.get("reframing_pressure", 0.0)) > 0.70
        or active_meta_quest is not None
    ):
        if active_meta_quest is not None or float(stabilized_pressure.get("reframing_pressure", 0.0)) > 0.75:
            genome_state = recombine(genome_state, None, stabilized_pressure)
        else:
            active_genome = mutate_domain_genome(active_genome, step=0.08)
            genome_state = active_genome.as_dict()
    domain_artifact_id = register_domain_artifact(
        {"genome": genome_state, "routing": routing},
        parent=parent,
        score=float(metrics.get("score", 0.0)),
        novelty=float(metrics.get("novelty", 0.0)),
        diversity=float(metrics.get("diversity", 0.0)),
        cost=float(metrics.get("cost", 0.0)),
    )
    artifact_id = register_quest_artifact(
        {"pressure": stabilized_pressure, "workers": new_workers, "genome": genome_state, "budgets": budgets, "routing": routing},
        parent=parent,
        score=float(metrics.get("score", 0.0)),
        novelty=float(metrics.get("novelty", 0.0)),
        diversity=float(metrics.get("diversity", 0.0)),
        cost=float(metrics.get("cost", 0.0)),
        quest=q,
        policy=new_policy,
    )
    save("pressure", raw_pressure)
    save("stabilized_pressure", stabilized_pressure)
    save("quest", q)
    save("policy", new_policy)
    save("policy_stack", policy_stack)
    save("evaluation", evaluation)
    save("guard", guard)
    save("stabilized_market", stabilized_market)
    save("cooldown", cooldown_state)
    if repair:
        save("repair", repair)
        remember("repair_artifact", repair)
    save("genome", genome_state)
    save("allocator", {"market": stabilized_market, "budgets": budgets})
    remember("pressure_snapshot", stabilized_pressure)
    remember("quest_artifact", {"artifact_id": artifact_id, "quest": q})
    remember("policy_artifact", {"artifact_id": policy_artifact_id, "policy": new_policy})
    remember("policy_stack_artifact", {"artifact_id": policy_stack_artifact_id, "policy_stack": policy_stack})
    remember("evaluation_artifact", {"artifact_id": evaluation_artifact_id, "evaluation": evaluation})
    remember("exploration_strategy_artifact", {"artifact_id": exploration_strategy_artifact_id, "strategy": exploration_strategy})
    remember("allocator_artifact", {"artifact_id": allocator_artifact_id, "budgets": budgets})
    remember("domain_genome_snapshot", {"artifact_id": domain_artifact_id, "genome": genome_state, "routing": routing})
    return {
        "artifact_id": artifact_id,
        "quest": q,
        "meta_quest": active_meta_quest,
        "policy": new_policy,
        "policy_stack": policy_stack,
        "policy_artifact_id": policy_artifact_id,
        "policy_stack_artifact_id": policy_stack_artifact_id,
        "evaluation_artifact_id": evaluation_artifact_id,
        "exploration_strategy_artifact_id": exploration_strategy_artifact_id,
        "allocator_artifact_id": allocator_artifact_id,
        "domain_artifact_id": domain_artifact_id,
        "evaluation": evaluation,
        "exploration_strategy": exploration_strategy,
        "guard": guard,
        "cooldown": cooldown_state,
        "repair": repair,
        "workers": new_workers,
        "pressure": raw_pressure,
        "stabilized_pressure": stabilized_pressure,
        "market": stabilized_market,
        "stabilized_market": stabilized_market,
        "budgets": budgets,
        "routing": routing,
        "domain": domain,
        "genome": genome_state,
    }
