from __future__ import annotations

from typing import Any

from federation.federation_state import federation_state
from genesis.replay import replay_state
from runtime.civilization_state import civilization_status as state_civilization_status
from runtime.civilization_memory import civilization_state
from runtime.genesis_ceiling import (
    CANONICAL_EXPLORATION_LOOP,
    DOMAIN_ECOLOGY,
    DOMINANCE_CAP,
    DOMINANCE_EMERGENCY,
    FAILURE_PROTOCOL_STATES,
    LINEAGE_ECOLOGY,
)
from runtime.lineage_ecology import assess_lineages
from runtime.replay_state import replay_ops_state
from runtime.runtime_safety import runtime_safety


def pressure_summary() -> dict[str, Any]:
    state = replay_state()
    summary = dict(state.get("pressure_state", {}))
    civ = civilization_state()
    for key in (
        "threshold_crossing_score",
        "breakout_acceleration_score",
        "tail_yield_score",
        "dominant_lock_in_risk",
        "resurrection_potential",
        "portfolio_concentration_risk",
        "policy_staleness_score",
        "exploration_entropy",
        "lineage_entropy",
        "innovation_density",
        "competition_pressure",
        "market_adoption_pressure",
        "platform_policy_pressure",
        "audience_feedback_pressure",
        "environment_volatility",
    ):
        summary[key] = float(civ.get(key, summary.get(key, 0.0)))
    return summary


def economy_summary() -> dict[str, Any]:
    state = replay_state()
    summary = dict(state.get("resource_allocation", {}))
    if not summary:
        summary = dict(state.get("exploration_economy_state", {}))
    return {
        "attention_budget": summary.get("attention_budget"),
        "exploration_budget": summary.get("exploration_budget", summary.get("budget")),
        "mutation_budget": summary.get("mutation_budget"),
        "selection_budget": summary.get("selection_budget"),
        "runtime_slots": summary.get("runtime_slots") or (summary.get("runtime_slot_allocation", {}) if isinstance(summary.get("runtime_slot_allocation"), dict) else {}).get("runtime_slots"),
        "selection_weights": dict(summary.get("selection_weights", {})) if isinstance(summary.get("selection_weights"), dict) else {},
        "budget_mix": dict(summary.get("budget_mix", {})) if isinstance(summary.get("budget_mix"), dict) else {},
        "economy_balance_score": float(summary.get("economy_balance_score", 0.0) or 0.0),
        "budget_skew": float(summary.get("budget_skew", 0.0) or 0.0),
        "diversity_allocation_budget": int(summary.get("diversity_allocation_budget", 0) or 0),
        "evaluation_diversity_budget": int(summary.get("evaluation_diversity_budget", 0) or 0),
        "rebalancing_actions": list(summary.get("rebalancing_actions", [])) if isinstance(summary.get("rebalancing_actions"), list) else [],
        "runtime_slot_allocation": dict(summary.get("runtime_slot_allocation", {})) if isinstance(summary.get("runtime_slot_allocation"), dict) else {},
        "memory_pressure": dict(summary.get("memory_pressure", {})) if isinstance(summary.get("memory_pressure"), dict) else {},
        "allocation_rationale": {
            "pressure": dict(state.get("pressure_state", {})) if isinstance(state.get("pressure_state"), dict) else {},
            "civilization_memory": civilization_state(),
        },
    }


def lineage_summary() -> dict[str, Any]:
    state = replay_state()
    lineage_state = state.get("lineage_state", {}) if isinstance(state.get("lineage_state"), dict) else {}
    rows = [{"lineage_id": key, "count": value} for key, value in dict(lineage_state.get("lineages", {})).items()]
    out = assess_lineages(rows or [{"lineage_id": "default"}], diversity_floor=2)
    out["surviving_lineages"] = int(lineage_state.get("surviving_lineages", out["surviving_lineages"]))
    out["lineage_concentration"] = float(lineage_state.get("lineage_concentration", out["lineage_concentration"]))
    civ = civilization_state()
    out["effective_lineage_diversity"] = float(civ.get("effective_lineage_diversity", out.get("effective_lineage_diversity", 0.0)))
    out["active_lineage_count"] = int(civ.get("active_lineage_count", out.get("active_lineage_count", 0)))
    out["dormant_lineage_count"] = int(civ.get("dormant_lineage_count", out.get("dormant_lineage_count", 0)))
    out["branch_rate"] = float(civ.get("branch_rate", 0.0))
    out["merge_rate"] = float(civ.get("merge_rate", 0.0))
    out["branch_pressure"] = float(civ.get("branch_pressure", 0.0))
    out["dominance_suppression"] = float(civ.get("dominance_suppression", 0.0))
    out["zombie_lineages"] = list(civ.get("zombie_lineages", out.get("zombie_lineages", []))) if isinstance(civ.get("zombie_lineages"), list) else out.get("zombie_lineages", [])
    return out


def domain_summary() -> dict[str, Any]:
    civ = civilization_state()
    domains = dict(civ.get("domain_distribution", {}))
    lifecycle = dict(civ.get("domain_lifecycle_state", {})) if isinstance(civ.get("domain_lifecycle_state"), dict) else {}
    return {
        "created_domains": list(civ.get("created_domains", [])),
        "active_domains": list(lifecycle.get("active_domains", civ.get("active_domains", []))),
        "inactive_domains": list(lifecycle.get("inactive_domains", civ.get("inactive_domains", []))),
        "retired_domains": list(lifecycle.get("retired_domains", civ.get("retired_domains", []))),
        "resurrectable_domains": list(lifecycle.get("resurrectable_domains", civ.get("resurrectable_domains", []))),
        "domain_distribution": domains,
        "domain_count": len(civ.get("created_domains", domains)),
        "domain_turnover": float(civ.get("domain_turnover", 0.0)),
        "domain_activation_rate": float(civ.get("domain_activation_rate", 0.0)),
        "domain_retirement_rate": float(civ.get("domain_retirement_rate", 0.0)),
        "domain_lineage_coverage": float(civ.get("domain_lineage_coverage", 0.0)),
        "domain_clusters": dict(civ.get("domain_clusters", {})),
        "domain_competition": float(civ.get("domain_competition_index", 0.0)),
        "domain_niches": dict(civ.get("domain_niches", {})),
    }


def civilization_summary() -> dict[str, Any]:
    return state_civilization_status()


def civilization_status() -> dict[str, Any]:
    return state_civilization_status()


def replay_summary() -> dict[str, Any]:
    state = replay_state()
    return {
        "tick": int(state.get("tick", 0)),
        "events": int(state.get("events", 0)),
        "metrics": int(state.get("metrics", 0)),
        "artifacts": int(state.get("artifacts", 0)),
        "replay_ok": bool(state),
        "replay_ops": replay_ops_state(),
    }


def runtime_summary() -> dict[str, Any]:
    civ = civilization_state()
    federation = federation_state()
    safety = runtime_safety()
    return {
        "canonical_loop": list(CANONICAL_EXPLORATION_LOOP),
        "canonical_ownership": {
            "genesis": "append-only truth, replay, invariant law, recovery law",
            "runtime": "canonical loop orchestration, replay-derived state, pressure, allocation, failure protocol",
            "artifact": "immutable registry, lineage, archive",
            "domains": "domain contracts, loaders, genomes, lifecycle hooks",
            "validation": "boundary, ownership, constitution, and artifact law gates",
            "observer": "read-only black-box projections",
        },
        "failure_protocol": {
            "states": list(FAILURE_PROTOCOL_STATES),
            "current_state": str(safety.get("failure_protocol_state", "plateau")),
            "lineage_floor": LINEAGE_ECOLOGY.minimum,
            "lineage_preferred": LINEAGE_ECOLOGY.preferred,
            "domain_floor": DOMAIN_ECOLOGY.minimum,
            "domain_preferred": DOMAIN_ECOLOGY.preferred,
            "dominance_cap": DOMINANCE_CAP,
            "dominance_emergency_threshold": DOMINANCE_EMERGENCY,
        },
        "replay": replay_summary(),
        "civilization": civilization_summary(),
        "lineages": lineage_summary(),
        "domains": domain_summary(),
        "federation": federation,
        "evaluations": {
            "active_evaluation_generations": int(civ.get("active_evaluation_generations", 0)),
            "dormant_evaluation_generations": int(civ.get("dormant_evaluation_generations", 0)),
            "retired_evaluation_generations": int(civ.get("retired_evaluation_generations", 0)),
            "evaluation_diversity": float(civ.get("evaluation_diversity", 0.0)),
            "evaluation_dominance_index": float(civ.get("evaluation_dominance_index", 0.0)),
            "active_evaluation_distribution": dict(civ.get("active_evaluation_distribution", {})),
        },
        "pressure": pressure_summary(),
        "ceiling": {
            "lineage_entropy": float(civ.get("lineage_entropy", 0.0)),
            "exploration_entropy": float(civ.get("exploration_entropy", 0.0)),
            "breakout_detection": float(civ.get("breakout_acceleration_score", 0.0)),
            "knowledge_density": float(civ.get("knowledge_density", 0.0)),
            "ceiling_proximity": float(civ.get("threshold_crossing_score", 0.0)),
            "tail_yield_score": float(civ.get("tail_yield_score", 0.0)),
        },
        "economy": economy_summary(),
        "safety": safety,
        "stability": {
            "stability_score": float(civ.get("stability_score", 0.0)),
            "drift_score": float(civ.get("drift_score", 0.0)),
            "stagnation_score": float(civ.get("stagnation_score", 0.0)),
            "overexpansion_score": float(civ.get("overexpansion_score", 0.0)),
            "underexploration_score": float(civ.get("underexploration_score", 0.0)),
            "concentration_streak": int(civ.get("concentration_streak", 0)),
            "diversification_intervention_count": int(civ.get("diversification_intervention_count", 0)),
            "forced_branch_count": int(civ.get("forced_branch_count", 0)),
            "stability_actions": list(civ.get("stability_actions", [])),
        },
        "policy_lineage": {
            "policy_generations": int(civ.get("policy_generations", 0)),
            "policy_staleness_score": float(civ.get("policy_staleness_score", 0.0)),
            "active_external_policies": int(civ.get("active_external_policies", 0)),
        },
    }


def economy_status() -> dict[str, Any]:
    return economy_summary()


def runtime_status() -> dict[str, Any]:
    return runtime_summary()


def lineage_status() -> dict[str, Any]:
    return lineage_summary()


def domain_status() -> dict[str, Any]:
    return domain_summary()


def stability_status() -> dict[str, Any]:
    civ = civilization_state()
    return {
        "stability_score": float(civ.get("stability_score", 0.0)),
        "drift_score": float(civ.get("drift_score", 0.0)),
        "stagnation_score": float(civ.get("stagnation_score", 0.0)),
        "overexpansion_score": float(civ.get("overexpansion_score", 0.0)),
        "underexploration_score": float(civ.get("underexploration_score", 0.0)),
        "stability_actions": list(civ.get("stability_actions", [])),
    }


def safety_status() -> dict[str, Any]:
    return runtime_safety()


def federation_summary() -> dict[str, Any]:
    return federation_state()


def node_summary() -> dict[str, Any]:
    federation = federation_state()
    topology = dict(federation.get("federation_topology", {}))
    return {
        "node_count": len(list(federation.get("federation_nodes", []))),
        "node_topology": topology,
        "artifact_exchange_rate": float(federation.get("artifact_exchange_rate", 0.0)),
        "domain_propagation_rate": float(federation.get("domain_propagation_rate", 0.0)),
        "policy_diffusion_rate": float(federation.get("policy_diffusion_rate", 0.0)),
        "knowledge_flow_rate": float(federation.get("knowledge_flow_rate", 0.0)),
    }


def federation_adoption_status() -> dict[str, Any]:
    federation = federation_state()
    return {
        "federation_adoption_rate": float(federation.get("federation_adoption_rate", 0.0)),
        "federation_activation_rate": float(federation.get("federation_activation_rate", 0.0)),
        "federation_influence_score": float(federation.get("federation_influence_score", 0.0)),
    }


def external_artifact_status() -> dict[str, Any]:
    federation = federation_state()
    return {
        "observed_external_artifacts": int(federation.get("observed_external_artifacts", 0)),
        "imported_external_artifacts": int(federation.get("imported_external_artifacts", 0)),
        "adopted_external_artifacts": int(federation.get("adopted_external_artifacts", 0)),
        "active_external_artifacts": int(federation.get("active_external_artifacts", 0)),
    }


def external_policy_status() -> dict[str, Any]:
    federation = federation_state()
    return {
        "observed_external_policies": int(federation.get("observed_external_policies", 0)),
        "adopted_external_policies": int(federation.get("adopted_external_policies", 0)),
        "active_external_policies": int(federation.get("active_external_policies", 0)),
        "policy_diffusion_rate": float(federation.get("policy_diffusion_rate", 0.0)),
    }


def external_domain_status() -> dict[str, Any]:
    federation = federation_state()
    return {
        "imported_domains": int(federation.get("imported_domains", 0)),
        "adopted_domains": int(federation.get("adopted_domains", 0)),
        "active_imported_domains": int(federation.get("active_imported_domains", 0)),
        "domain_propagation_rate": float(federation.get("domain_propagation_rate", 0.0)),
    }


def transport_status() -> dict[str, Any]:
    federation = federation_state()
    return {
        "send_queue_depth": int(federation.get("send_queue_depth", 0)),
        "receive_queue_depth": int(federation.get("receive_queue_depth", 0)),
        "adoption_queue_depth": int(federation.get("adoption_queue_depth", 0)),
        "transport_delivery_rate": float(federation.get("transport_delivery_rate", 0.0)),
        "adoption_completion_rate": float(federation.get("adoption_completion_rate", 0.0)),
    }


def hydration_status() -> dict[str, Any]:
    federation = federation_state()
    return {
        "mirrored_external_artifacts": int(federation.get("mirrored_external_artifacts", 0)),
        "active_mirrored_artifacts": int(federation.get("active_mirrored_artifacts", 0)),
        "hydration_rate": float(federation.get("hydration_rate", 0.0)),
        "hydration_depth_distribution": dict(federation.get("hydration_depth_distribution", {})),
        "mirror_lineage_count": int(federation.get("mirror_lineage_count", 0)),
    }


def mirrored_artifact_status() -> dict[str, Any]:
    federation = federation_state()
    return {
        "mirrored_external_artifacts": int(federation.get("mirrored_external_artifacts", 0)),
        "active_mirrored_artifacts": int(federation.get("active_mirrored_artifacts", 0)),
        "foreign_origin_distribution": dict(federation.get("foreign_origin_distribution", {})),
    }


def foreign_origin_status() -> dict[str, Any]:
    federation = federation_state()
    return {
        "foreign_origin_distribution": dict(federation.get("foreign_origin_distribution", {})),
        "federation_monoculture_score": float(federation.get("federation_monoculture_score", 0.0)),
    }


def hydration_guardrail_status() -> dict[str, Any]:
    safety = runtime_safety()
    return {
        "hydration_rate": float(safety.get("hydration_rate", 0.0)),
        "federation_monoculture_score": float(safety.get("federation_monoculture_score", 0.0)),
        "federation_safety_actions": list(safety.get("federation_safety_actions", [])),
    }


__all__ = [
    "civilization_summary",
    "civilization_status",
    "domain_summary",
    "domain_status",
    "economy_summary",
    "federation_summary",
    "federation_adoption_status",
    "external_artifact_status",
    "external_policy_status",
    "external_domain_status",
    "foreign_origin_status",
    "node_summary",
    "transport_status",
    "hydration_status",
    "mirrored_artifact_status",
    "hydration_guardrail_status",
    "economy_status",
    "lineage_summary",
    "lineage_status",
    "pressure_summary",
    "replay_summary",
    "safety_status",
    "stability_status",
    "runtime_summary",
    "runtime_status",
]
