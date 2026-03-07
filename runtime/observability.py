from __future__ import annotations

from typing import Any

from federation.federation_state import federation_state
from genesis.replay import replay_state
from runtime.civilization_state import civilization_status as state_civilization_status
from runtime.civilization_memory import civilization_state
from runtime.lineage_ecology import assess_lineages
from runtime.runtime_safety import runtime_safety


def pressure_summary() -> dict[str, Any]:
    state = replay_state()
    return dict(state.get("pressure_state", {}))


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
    }


def runtime_summary() -> dict[str, Any]:
    civ = civilization_state()
    return {
        "replay": replay_summary(),
        "civilization": civilization_summary(),
        "lineages": lineage_summary(),
        "domains": domain_summary(),
        "federation": federation_state(),
        "evaluations": {
            "active_evaluation_generations": int(civ.get("active_evaluation_generations", 0)),
            "dormant_evaluation_generations": int(civ.get("dormant_evaluation_generations", 0)),
            "retired_evaluation_generations": int(civ.get("retired_evaluation_generations", 0)),
            "evaluation_diversity": float(civ.get("evaluation_diversity", 0.0)),
            "evaluation_dominance_index": float(civ.get("evaluation_dominance_index", 0.0)),
            "active_evaluation_distribution": dict(civ.get("active_evaluation_distribution", {})),
        },
        "pressure": pressure_summary(),
        "economy": economy_summary(),
        "safety": runtime_safety(),
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


__all__ = [
    "civilization_summary",
    "civilization_status",
    "domain_summary",
    "domain_status",
    "economy_summary",
    "federation_summary",
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
