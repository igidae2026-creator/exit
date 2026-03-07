from __future__ import annotations

import os
from typing import Any

from genesis.replay import replay_state
from runtime.civilization_memory import civilization_state
from runtime.civilization_state import civilization_state as build_civilization_state
from runtime.observability import domain_summary, economy_summary, lineage_summary, safety_status, stability_status
from runtime.profiles import runtime_profile
from runtime.runtime_safety import runtime_safety
from runtime.soak_runner import run_soak


def _observed_budget_cycles(soak_ticks: list[dict[str, Any]]) -> int:
    cycles = 0
    depth = 0
    for row in soak_ticks:
        cycle = row.get("exploration_cycle", {}) if isinstance(row.get("exploration_cycle"), dict) else {}
        if bool(cycle.get("exhausted")):
            cycles += 1
            depth = 0
            continue
        budget = int(cycle.get("limit", cycle.get("exploration_budget", 1)) or 1)
        quest = row.get("quest", {}) if isinstance(row.get("quest"), dict) else {}
        if str(quest.get("type", "")) == "exploration":
            depth += 1
            if depth >= max(1, budget):
                cycles += 1
                depth = 0
    return cycles


def run_long_run_validation(*, ticks: int = 120, seed: int = 42, fail_open: bool = True, profile: str = "smoke") -> dict[str, Any]:
    os.environ.setdefault("METAOS_SOAK_FAST", "1")
    profile_spec = runtime_profile(profile)
    soak_ticks, summary = run_soak(ticks=ticks, seed=seed, fail_open=fail_open)
    observed_budget_cycle_count = max(int(summary.get("budget_cycle_count", 0)), _observed_budget_cycles(list(soak_ticks)))
    replay = replay_state()
    civ = civilization_state()
    civ_state = build_civilization_state()
    lineages = lineage_summary()
    domains = domain_summary()
    economy = economy_summary()
    safety = runtime_safety(profile=profile_spec.name)
    stability = stability_status()
    safety_view = safety_status()
    summary = {**summary, "budget_cycle_count": observed_budget_cycle_count}
    artifact_population = dict(civ_state.get("artifact_population", {}))
    policy_population = dict(civ_state.get("policy_population", {}))
    domain_population = dict(civ_state.get("domain_population", {}))
    healthy = (
        bool(replay)
        and float(civ.get("memory_growth", 0.0)) > 0.0
        and float(civ.get("knowledge_density", 0.0)) > 0.0
        and int(policy_population.get("generations", 0)) >= profile_spec.target_policy_generations
        and float(civ_state.get("stability_score", 0.0)) > 0.2
        and float(civ_state.get("economy_balance_score", 0.0)) > 0.2
        and int(civ_state.get("active_lineage_count", 0)) >= profile_spec.target_surviving_lineages
        and int(civ_state.get("evaluation_generations", 0)) >= profile_spec.target_evaluation_generations
        and int(domains.get("domain_count", 0)) >= profile_spec.target_active_domains
    )
    return {
        "profile": profile_spec.name,
        "profile_targets": {
            "surviving_lineages": profile_spec.target_surviving_lineages,
            "active_domains": profile_spec.target_active_domains,
            "policy_generations": profile_spec.target_policy_generations,
            "evaluation_generations": profile_spec.target_evaluation_generations,
            "replay_event_floor": profile_spec.replay_event_floor,
        },
        "ticks": len(soak_ticks),
        "summary": summary,
        "replay_ok": bool(replay),
        "civilization_state": civ,
        "civilization_runtime_state": civ_state,
        "lineages": lineages,
        "domains": domains,
        "runtime_safety": safety,
        "safety_status": safety_view,
        "economy": economy,
        "stability": stability,
        "memory_growth": float(civ.get("memory_growth", 0.0)),
        "surviving_lineages": int(lineages.get("surviving_lineages", 0)),
        "domain_count": int(domains.get("domain_count", 0)),
        "budget_cycle_count": observed_budget_cycle_count,
        "stability_score": float(civ_state.get("stability_score", 0.0)),
        "economy_balance_score": float(civ_state.get("economy_balance_score", 0.0)),
        "active_lineage_count": int(civ_state.get("active_lineage_count", 0)),
        "dormant_lineage_count": int(civ_state.get("dormant_lineage_count", 0)),
        "effective_lineage_diversity": float(civ_state.get("effective_lineage_diversity", 0.0)),
        "dominance_index": float(civ_state.get("dominance_index", 0.0)),
        "branch_rate": float(civ_state.get("branch_rate", 0.0)),
        "domain_activation_rate": float(civ_state.get("domain_activation_rate", 0.0)),
        "domain_retirement_rate": float(civ_state.get("domain_retirement_rate", 0.0)),
        "evaluation_generations": int(civ_state.get("evaluation_generations", 0)),
        "active_evaluation_generations": int(civ_state.get("active_evaluation_generations", 0)),
        "dormant_evaluation_generations": int(civ_state.get("dormant_evaluation_generations", 0)),
        "retired_evaluation_generations": int(civ_state.get("retired_evaluation_generations", 0)),
        "evaluation_diversity": float(civ_state.get("evaluation_diversity", 0.0)),
        "evaluation_dominance_index": float(civ_state.get("evaluation_dominance_index", 0.0)),
        "policy_turnover_quality": float(civ_state.get("policy_turnover_quality", 0.0)),
        "evaluation_turnover_quality": float(civ_state.get("evaluation_turnover_quality", 0.0)),
        "evaluation_branch_rate": float(civ_state.get("evaluation_branch_rate", 0.0)),
        "evaluation_retirement_rate": float(civ_state.get("evaluation_retirement_rate", 0.0)),
        "evaluation_reactivation_rate": float(civ_state.get("evaluation_reactivation_rate", 0.0)),
        "active_evaluation_distribution": dict(civ_state.get("active_evaluation_distribution", {})),
        "diversity_allocation_budget": int(civ_state.get("diversity_allocation_budget", 0)),
        "diversification_intervention_count": int(civ_state.get("diversification_intervention_count", 0)),
        "forced_branch_count": int(civ_state.get("forced_branch_count", 0)),
        "domain_lineage_coverage": float(civ_state.get("domain_lineage_coverage", 0.0)),
        "guardrail_actions": list(civ_state.get("guardrail_actions", [])),
        "artifact_population_changed": bool(artifact_population),
        "policy_population_evolved": int(policy_population.get("generations", 0)) > 0,
        "knowledge_density_increased": float(civ.get("knowledge_density", 0.0)) > 0.0,
        "domains_expanded": len(domain_population) > 1 or int(summary.get("new_domain_count", 0)) > 0,
        "healthy": healthy,
    }


def validate_long_run(*, ticks: int = 120, seed: int = 42, fail_open: bool = True, profile: str = "smoke") -> dict[str, Any]:
    return run_long_run_validation(ticks=ticks, seed=seed, fail_open=fail_open, profile=profile)


__all__ = ["run_long_run_validation", "validate_long_run"]
