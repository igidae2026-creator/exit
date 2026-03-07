from __future__ import annotations

import os
from typing import Any

from genesis.replay import replay_state
from runtime.civilization_memory import civilization_state
from runtime.civilization_state import civilization_state as build_civilization_state
from runtime.observability import domain_summary, economy_summary, lineage_summary, safety_status, stability_status
from runtime.observability import (
    domain_summary,
    economy_summary,
    lineage_summary,
    safety_status,
    stability_status,
)
from runtime.runtime_safety import runtime_safety
from runtime.soak_runner import run_soak

LONG_RUN_TIERS: dict[str, dict[str, int]] = {
    "smoke": {"ticks": 256},
    "bounded": {"ticks": 4096},
    "soak": {"ticks": 50000},
}

_MIN_FLOORS: dict[str, dict[str, float]] = {
    "smoke": {
        "active_lineage_count": 2,
        "active_domain_count": 2,
        "stability_score": 0.30,
        "economy_balance_score": 0.30,
        "domain_lineage_coverage": 0.15,
        "evaluation_diversity": 0.15,
        "dominance_index_max": 0.85,
    },
    "bounded": {
        "active_lineage_count": 4,
        "active_domain_count": 3,
        "stability_score": 0.60,
        "economy_balance_score": 0.60,
        "domain_lineage_coverage": 0.50,
        "evaluation_diversity": 0.40,
        "dominance_index_max": 0.50,
    },
    "soak": {
        "active_lineage_count": 8,
        "active_domain_count": 6,
        "stability_score": 0.75,
        "economy_balance_score": 0.70,
        "domain_lineage_coverage": 0.75,
        "evaluation_diversity": 0.60,
        "dominance_index_max": 0.35,
    },
}

LONG_RUN_HORIZONS: dict[str, int] = {
    "smoke": 2_000,
    "stability": 20_000,
    "endurance": 100_000,
}

PROFILE_FLOORS: dict[str, dict[str, float]] = {
    "smoke": {
        "surviving_lineages": 4,
        "active_domains": 3,
        "policy_generations": 25,
        "evaluation_generations": 15,
        "max_dominance_index": 0.35,
    },
    "stability": {
        "surviving_lineages": 8,
        "active_domains": 5,
        "policy_generations": 200,
        "evaluation_generations": 140,
        "max_dominance_index": 0.35,
    },
    "endurance": {
        "surviving_lineages": 8,
        "active_domains": 5,
        "policy_generations": 1_000,
        "evaluation_generations": 700,
        "max_dominance_index": 0.35,
    },
}


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


def _profile_acceptance(profile: str, payload: dict[str, Any]) -> dict[str, Any]:
    floors = PROFILE_FLOORS.get(profile)
    if not floors:
        return {"profile": profile, "recognized": False, "accepted": False, "checks": {}}

    surviving_lineages = int(payload.get("surviving_lineages", 0))
    active_domains = int(payload.get("domain_count", 0))
    policy_generations = int(payload.get("civilization_state", {}).get("policy_generations", 0))
    evaluation_generations = int(payload.get("evaluation_generations", 0))
    dominance_index = float(payload.get("dominance_index", 1.0))

    checks = {
        "replay_ok": bool(payload.get("replay_ok")),
        "surviving_lineages": surviving_lineages >= int(floors["surviving_lineages"]),
        "active_domains": active_domains >= int(floors["active_domains"]),
        "policy_generations": policy_generations >= int(floors["policy_generations"]),
        "evaluation_generations": evaluation_generations >= int(floors["evaluation_generations"]),
        "dominance_index": dominance_index <= float(floors["max_dominance_index"]),
    }
    return {
        "profile": profile,
        "recognized": True,
        "accepted": all(checks.values()),
        "checks": checks,
        "floors": floors,
    }


def run_long_run_validation(*, ticks: int = 120, seed: int = 42, fail_open: bool = True, profile: str = "") -> dict[str, Any]:
    os.environ.setdefault("METAOS_SOAK_FAST", "1")
    from runtime.soak_runner import run_soak

    soak_ticks, summary = run_soak(ticks=ticks, seed=seed, fail_open=fail_open)
def _resolve_tier(ticks: int, tier: str | None) -> tuple[str, int]:
    if tier:
        canonical = tier.lower().strip()
        if canonical not in LONG_RUN_TIERS:
            raise ValueError(f"unknown long-run tier: {tier}")
        return canonical, LONG_RUN_TIERS[canonical]["ticks"]
    return "custom", max(1, int(ticks))


def _tier_health(payload: dict[str, Any], *, tier: str) -> bool:
    floors = _MIN_FLOORS.get(tier)
    if not floors:
        return bool(payload.get("healthy_smoke"))
    return (
        bool(payload.get("replay_ok"))
        and int(payload.get("append_only_violation_count", 0)) == 0
        and int(payload.get("invariant_violation_count", 0)) == 0
        and int(payload.get("replay_mismatch_count", 0)) == 0
        and int(payload.get("active_lineage_count", 0)) >= int(floors["active_lineage_count"])
        and int(payload.get("domain_count", 0)) >= int(floors["active_domain_count"])
        and float(payload.get("stability_score", 0.0)) >= float(floors["stability_score"])
        and float(payload.get("economy_balance_score", 0.0)) >= float(floors["economy_balance_score"])
        and float(payload.get("domain_lineage_coverage", 0.0)) >= float(floors["domain_lineage_coverage"])
        and float(payload.get("evaluation_diversity", 0.0)) >= float(floors["evaluation_diversity"])
        and float(payload.get("dominance_index", 1.0)) <= float(floors["dominance_index_max"])
        and bool(payload.get("policy_population_evolved"))
        and int(payload.get("active_evaluation_generations", 0)) > 1
        and bool(payload.get("domains_expanded"))
    )


def run_long_run_validation(
    *, ticks: int = 256, seed: int = 42, fail_open: bool = True, tier: str | None = None
) -> dict[str, Any]:
    os.environ.setdefault("METAOS_SOAK_FAST", "1")
    resolved_tier, resolved_ticks = _resolve_tier(ticks, tier)
    soak_ticks, summary = run_soak(ticks=resolved_ticks, seed=seed, fail_open=fail_open)
    observed_budget_cycle_count = max(int(summary.get("budget_cycle_count", 0)), _observed_budget_cycles(list(soak_ticks)))
    replay = replay_state()
    civ = civilization_state()
    civ_state = build_civilization_state()
    lineages = lineage_summary()
    domains = domain_summary()
    economy = economy_summary()
    safety = runtime_safety()
    stability = stability_status()
    safety_view = safety_status()
    summary = {**summary, "budget_cycle_count": observed_budget_cycle_count}
    artifact_population = dict(civ_state.get("artifact_population", {}))
    policy_population = dict(civ_state.get("policy_population", {}))
    domain_population = dict(civ_state.get("domain_population", {}))
    payload = {
    invariant_violations = int(len(civ_state.get("invariant_violations", [])))
    append_only_violations = int(len(civ_state.get("append_only_violations", [])))
    replay_mismatches = int(len(civ_state.get("replay_mismatches", [])))

    out = {
        "ticks": len(soak_ticks),
        "requested_ticks": int(ticks),
        "resolved_ticks": resolved_ticks,
        "tier": resolved_tier,
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
        "append_only_violation_count": append_only_violations,
        "invariant_violation_count": invariant_violations,
        "replay_mismatch_count": replay_mismatches,
        "artifact_population_changed": bool(artifact_population),
        "policy_population_evolved": int(policy_population.get("generations", 0)) > 0,
        "knowledge_density_increased": float(civ.get("knowledge_density", 0.0)) > 0.0,
        "domains_expanded": len(domain_population) > 1 or int(summary.get("new_domain_count", 0)) > 0,
    }
    payload["profile_acceptance"] = _profile_acceptance(profile, payload) if profile else None
    return payload
    out["healthy_smoke"] = (
        bool(out["replay_ok"])
        and out["append_only_violation_count"] == 0
        and out["invariant_violation_count"] == 0
        and out["replay_mismatch_count"] == 0
        and out["memory_growth"] > 0.0
        and bool(out["policy_population_evolved"])
    )
    out["healthy"] = _tier_health(out, tier=resolved_tier if resolved_tier in _MIN_FLOORS else "smoke")
    return out


def validate_long_run(
    *, ticks: int = 256, seed: int = 42, fail_open: bool = True, tier: str | None = None
) -> dict[str, Any]:
    return run_long_run_validation(ticks=ticks, seed=seed, fail_open=fail_open, tier=tier)


__all__ = ["LONG_RUN_HORIZONS", "run_long_run_validation", "validate_long_run"]
__all__ = ["LONG_RUN_TIERS", "run_long_run_validation", "validate_long_run"]
