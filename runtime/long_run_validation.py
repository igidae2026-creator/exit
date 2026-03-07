from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from genesis.replay import replay_state
from runtime.civilization_memory import civilization_state as memory_civilization_state
from runtime.civilization_state import civilization_state as runtime_civilization_state
from runtime.observability import (
    domain_summary,
    economy_summary,
    lineage_summary,
    safety_status,
    stability_status,
)
from runtime.profiles import RuntimeProfile, runtime_profile
from runtime.runtime_safety import runtime_safety
from runtime.soak_runner import run_soak


LONG_RUN_TIERS: dict[str, dict[str, int]] = {
    "smoke": {"ticks": 256},
    "bootstrap": {"ticks": 1_000},
    "bounded": {"ticks": 4_096},
    "aggressive": {"ticks": 5_000},
    "soak": {"ticks": 50_000},
    "production": {"ticks": 100_000},
}


@dataclass(frozen=True, slots=True)
class ValidationProfile:
    name: str
    min_ticks: int
    min_surviving_lineages: int
    min_active_domains: int
    min_policy_generations: int
    min_health_score: float


PROFILE_TABLE: dict[str, ValidationProfile] = {
    "smoke": ValidationProfile("smoke", 1_024, 4, 3, 8, 0.70),
    "bootstrap": ValidationProfile("bootstrap", 1_000, 4, 3, 12, 0.70),
    "aggressive": ValidationProfile("aggressive", 5_000, 6, 4, 24, 0.72),
    "soak": ValidationProfile("soak", 50_000, 8, 4, 32, 0.75),
    "production": ValidationProfile("production", 100_000, 8, 4, 32, 0.75),
    "endurance": ValidationProfile("endurance", 100_000, 16, 8, 64, 0.80),
    "civilization": ValidationProfile("civilization", 100_000, 16, 8, 64, 0.80),
}


_TIER_FLOORS: dict[str, dict[str, float]] = {
    "smoke": {
        "active_lineage_count": 2,
        "active_domain_count": 2,
        "stability_score": 0.30,
        "economy_balance_score": 0.30,
        "domain_lineage_coverage": 0.15,
        "evaluation_diversity": 0.15,
        "dominance_index_max": 0.85,
    },
    "bootstrap": {
        "active_lineage_count": 4,
        "active_domain_count": 3,
        "stability_score": 0.55,
        "economy_balance_score": 0.50,
        "domain_lineage_coverage": 0.45,
        "evaluation_diversity": 0.35,
        "dominance_index_max": 0.55,
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
    "aggressive": {
        "active_lineage_count": 6,
        "active_domain_count": 4,
        "stability_score": 0.70,
        "economy_balance_score": 0.65,
        "domain_lineage_coverage": 0.55,
        "evaluation_diversity": 0.45,
        "dominance_index_max": 0.45,
    },
    "soak": {
        "active_lineage_count": 8,
        "active_domain_count": 4,
        "stability_score": 0.75,
        "economy_balance_score": 0.70,
        "domain_lineage_coverage": 0.75,
        "evaluation_diversity": 0.60,
        "dominance_index_max": 0.35,
    },
    "production": {
        "active_lineage_count": 8,
        "active_domain_count": 4,
        "stability_score": 0.75,
        "economy_balance_score": 0.70,
        "domain_lineage_coverage": 0.75,
        "evaluation_diversity": 0.60,
        "dominance_index_max": 0.35,
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


def _resolve_request(
    *, profile: str | None, tier: str | None, ticks: int | None
) -> tuple[str, RuntimeProfile, ValidationProfile, str, int]:
    profile_name = (profile or "").strip().lower()
    tier_name = (tier or "").strip().lower()
    if tier_name:
        if tier_name not in LONG_RUN_TIERS:
            raise ValueError(f"unknown long-run tier: {tier}")
        resolved_ticks = LONG_RUN_TIERS[tier_name]["ticks"] if ticks is None else max(1, int(ticks))
        resolved_profile_name = profile_name or tier_name
        if resolved_profile_name == "bounded":
            resolved_profile_name = "aggressive"
        profile_spec = runtime_profile(resolved_profile_name)
        validation = PROFILE_TABLE.get(resolved_profile_name, PROFILE_TABLE["smoke"])
        return resolved_profile_name, profile_spec, validation, tier_name, resolved_ticks

    resolved_profile_name = profile_name or "smoke"
    profile_spec = runtime_profile(resolved_profile_name)
    validation = PROFILE_TABLE.get(resolved_profile_name, PROFILE_TABLE["smoke"])
    default_ticks = validation.min_ticks if ticks is None else max(1, int(ticks))
    resolved_ticks = max(validation.min_ticks, default_ticks)
    return resolved_profile_name, profile_spec, validation, "custom", resolved_ticks


def _profile_acceptance(profile: str, payload: dict[str, Any]) -> dict[str, Any]:
    floors = PROFILE_TABLE.get(profile)
    if floors is None:
        return {"profile": profile, "recognized": False, "accepted": False, "checks": {}}
    checks = {
        "ticks": int(payload.get("ticks", 0)) >= floors.min_ticks,
        "replay_ok": bool(payload.get("replay_ok")),
        "surviving_lineages": int(payload.get("surviving_lineages", 0)) >= floors.min_surviving_lineages,
        "active_domains": int(payload.get("domain_count", 0)) >= floors.min_active_domains,
        "policy_generations": int(payload.get("civilization_runtime_state", {}).get("policy_population", {}).get("generations", 0))
        >= floors.min_policy_generations,
        "stability_score": float(payload.get("stability_score", 0.0)) >= floors.min_health_score,
        "economy_balance_score": float(payload.get("economy_balance_score", 0.0)) >= floors.min_health_score,
    }
    return {
        "profile": profile,
        "recognized": True,
        "accepted": all(checks.values()),
        "checks": checks,
        "floors": {
            "ticks": floors.min_ticks,
            "surviving_lineages": floors.min_surviving_lineages,
            "active_domains": floors.min_active_domains,
            "policy_generations": floors.min_policy_generations,
            "health_score": floors.min_health_score,
        },
    }


def _tier_health(payload: dict[str, Any], *, tier: str) -> bool:
    if tier == "custom":
        return bool(payload.get("healthy_smoke"))
    floors = _TIER_FLOORS[tier]
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
        and int(payload.get("active_evaluation_generations", 0)) > 0
    )


def run_long_run_validation(
    *,
    profile: str | None = None,
    ticks: int | None = None,
    seed: int = 42,
    fail_open: bool = False,
    tier: str | None = None,
) -> dict[str, Any]:
    os.environ.setdefault("METAOS_SOAK_FAST", "1")
    resolved_profile_name, profile_spec, validation_spec, resolved_tier, resolved_ticks = _resolve_request(
        profile=profile, tier=tier, ticks=ticks
    )
    soak_ticks, soak_summary = run_soak(ticks=resolved_ticks, seed=seed, fail_open=fail_open)
    replay = replay_state()
    civ_memory = memory_civilization_state()
    civ_state = runtime_civilization_state()
    lineages = lineage_summary()
    domains = domain_summary()
    economy = economy_summary()
    safety = runtime_safety(profile=profile_spec.name)
    stability = stability_status()
    safety_view = safety_status()

    observed_budget_cycle_count = max(
        int(soak_summary.get("budget_cycle_count", 0)),
        _observed_budget_cycles(list(soak_ticks)),
    )
    summary = {**soak_summary, "budget_cycle_count": observed_budget_cycle_count}

    policy_population = dict(civ_state.get("policy_population", {}))
    artifact_population = dict(civ_state.get("artifact_population", {}))
    domain_population = dict(civ_state.get("domain_population", {}))

    stability_score = float(civ_state.get("stability_score", 0.0))
    economy_balance_score = float(civ_state.get("economy_balance_score", 0.0))
    surviving_lineages = int(lineages.get("surviving_lineages", 0))
    domain_count = int(domains.get("domain_count", 0))
    policy_generations = int(policy_population.get("generations", 0))
    invariant_violations = int(len(civ_state.get("invariant_violations", [])))
    append_only_violations = int(len(civ_state.get("append_only_violations", [])))
    replay_mismatches = int(len(civ_state.get("replay_mismatches", [])))

    threshold_checks = {
        "ticks": len(soak_ticks) >= validation_spec.min_ticks,
        "surviving_lineages": surviving_lineages >= validation_spec.min_surviving_lineages,
        "active_domains": domain_count >= validation_spec.min_active_domains,
        "policy_generations": policy_generations >= validation_spec.min_policy_generations,
        "stability_score": stability_score >= validation_spec.min_health_score,
        "economy_balance_score": economy_balance_score >= validation_spec.min_health_score,
        "replay_ok": bool(replay),
    }

    payload = {
        "profile": resolved_profile_name,
        "profile_requirements": {
            "ticks": validation_spec.min_ticks,
            "surviving_lineages": validation_spec.min_surviving_lineages,
            "active_domains": validation_spec.min_active_domains,
            "policy_generations": validation_spec.min_policy_generations,
            "health_score": validation_spec.min_health_score,
        },
        "profile_targets": {
            "ticks": profile_spec.target_ticks,
            "surviving_lineages": profile_spec.target_surviving_lineages,
            "active_domains": profile_spec.target_active_domains,
            "policy_generations": profile_spec.target_policy_generations,
            "evaluation_generations": profile_spec.target_evaluation_generations,
            "replay_event_floor": profile_spec.replay_event_floor,
        },
        "ticks": len(soak_ticks),
        "requested_ticks": int(ticks) if ticks is not None else None,
        "resolved_ticks": resolved_ticks,
        "tier": resolved_tier,
        "summary": summary,
        "replay_ok": bool(replay),
        "civilization_state": civ_memory,
        "civilization_runtime_state": civ_state,
        "lineages": lineages,
        "domains": domains,
        "runtime_safety": safety,
        "safety_status": safety_view,
        "economy": economy,
        "stability": stability,
        "memory_growth": float(civ_memory.get("memory_growth", 0.0)),
        "knowledge_density": float(civ_memory.get("knowledge_density", 0.0)),
        "surviving_lineages": surviving_lineages,
        "domain_count": domain_count,
        "budget_cycle_count": observed_budget_cycle_count,
        "stability_score": stability_score,
        "economy_balance_score": economy_balance_score,
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
        "policy_population_evolved": policy_generations > 0,
        "knowledge_density_increased": float(civ_memory.get("knowledge_density", 0.0)) > 0.0,
        "domains_expanded": len(domain_population) > 1 or int(summary.get("new_domain_count", 0)) > 0,
        "threshold_checks": threshold_checks,
    }
    payload["profile_acceptance"] = _profile_acceptance(resolved_profile_name, payload)
    payload["healthy_smoke"] = (
        bool(payload["replay_ok"])
        and payload["append_only_violation_count"] == 0
        and payload["invariant_violation_count"] == 0
        and payload["replay_mismatch_count"] == 0
        and payload["memory_growth"] > 0.0
        and bool(payload["policy_population_evolved"])
    )
    payload["healthy"] = _tier_health(payload, tier=resolved_tier)
    return payload


def validate_long_run(
    *,
    profile: str | None = None,
    ticks: int | None = None,
    seed: int = 42,
    fail_open: bool = False,
    tier: str | None = None,
) -> dict[str, Any]:
    return run_long_run_validation(
        profile=profile,
        ticks=ticks,
        seed=seed,
        fail_open=fail_open,
        tier=tier,
    )


__all__ = [
    "LONG_RUN_TIERS",
    "PROFILE_TABLE",
    "ValidationProfile",
    "run_long_run_validation",
    "validate_long_run",
]
