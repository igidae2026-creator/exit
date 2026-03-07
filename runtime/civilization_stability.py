from __future__ import annotations

from typing import Any, Mapping


def civilization_stability(
    ecology: Mapping[str, Any],
    civilization: Mapping[str, Any],
    memory: Mapping[str, float],
) -> dict[str, Any]:
    ecology_state = dict(ecology or {})
    civilization_state = dict(civilization or {})
    memory_state = dict(memory or {})
    lineage_counts = dict(civilization_state.get("lineage_counts", {})) if isinstance(civilization_state.get("lineage_counts"), Mapping) else {}
    domain_counts = dict(civilization_state.get("active_domain_distribution", civilization_state.get("domain_counts", {}))) if isinstance(civilization_state.get("active_domain_distribution", civilization_state.get("domain_counts", {})), Mapping) else {}
    policy_turnover = int(civilization_state.get("policy_generations", 0))
    diversity_index = round(
        0.5 * float(ecology_state.get("diversity_health", 0.5)) + 0.5 * float(ecology_state.get("exploration_health", 0.5)),
        4,
    )
    lineage_survival = len(lineage_counts)
    domain_growth = len(domain_counts)
    total_lineages = sum(lineage_counts.values()) or 1
    dominance_index = round(max(lineage_counts.values(), default=0) / total_lineages, 4)
    lineage_survival_rate = round(lineage_survival / max(1, total_lineages), 4)
    memory_growth = round(float(memory_state.get("memory_growth", 0.0)), 4)
    stable = diversity_index > 0.45 and lineage_survival > 1 and policy_turnover > 0 and domain_growth > 1 and memory_growth > 0.0 and dominance_index < 0.85
    governor_actions: list[str] = []
    if diversity_index < 0.45 or lineage_survival <= 1 or dominance_index >= 0.85:
        governor_actions.append("increase_diversity_pressure")
        governor_actions.append("force_reframing")
    if domain_growth <= 1:
        governor_actions.append("spawn_exploration_quest")
        governor_actions.append("reduce_expansion_rate")
    if memory_growth < 0.1:
        governor_actions.append("rebalance_resource_allocation")
    concentration_streak = int(civilization_state.get("concentration_streak", 0))
    diversification_intervention_count = int(civilization_state.get("diversification_intervention_count", 0))
    forced_branch_count = int(civilization_state.get("forced_branch_count", 0))
    if concentration_streak >= 6:
        governor_actions.extend(
            [
                "force_branching_pressure",
                "force_evaluation_diversification",
                "reduce_dominant_lineage_allocation",
                "increase_dormant_activation_attempts",
            ]
        )
        diversification_intervention_count += 1
        forced_branch_count += 1
    active_lineages = int(civilization_state.get("active_lineage_count", lineage_survival))
    dormant_lineages = int(civilization_state.get("dormant_lineage_count", max(0, lineage_survival - active_lineages)))
    effective_diversity = float(civilization_state.get("effective_lineage_diversity", ecology_state.get("lineage_diversity", diversity_index)))
    return {
        "diversity_index": diversity_index,
        "lineage_survival": lineage_survival,
        "lineage_survival_rate": lineage_survival_rate,
        "dominance_index": dominance_index,
        "effective_lineage_diversity": round(effective_diversity, 4),
        "active_lineage_count": active_lineages,
        "dormant_lineage_count": dormant_lineages,
        "concentration_streak": concentration_streak,
        "diversification_intervention_count": diversification_intervention_count,
        "forced_branch_count": forced_branch_count,
        "policy_turnover": policy_turnover,
        "domain_growth": domain_growth,
        "active_domain_count": int(civilization_state.get("active_domain_count", domain_growth)),
        "inactive_domain_count": len(list(civilization_state.get("inactive_domains", []))) if isinstance(civilization_state.get("inactive_domains"), list) else 0,
        "memory_growth": memory_growth,
        "stable": stable,
        "unstable": not stable,
        "governor_actions": governor_actions,
        "rebalance_required": not stable,
    }


__all__ = ["civilization_stability"]
