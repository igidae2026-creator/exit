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
    domain_counts = dict(civilization_state.get("domain_counts", {})) if isinstance(civilization_state.get("domain_counts"), Mapping) else {}
    policy_turnover = int(civilization_state.get("policy_generations", 0))
    diversity_index = round(
        0.5 * float(ecology_state.get("diversity_health", 0.5)) + 0.5 * float(ecology_state.get("exploration_health", 0.5)),
        4,
    )
    lineage_survival = len(lineage_counts)
    domain_growth = len(domain_counts)
    stable = diversity_index > 0.45 and lineage_survival > 1 and policy_turnover > 0 and domain_growth > 1 and float(memory_state.get("memory_growth", 0.0)) > 0.0
    governor_actions: list[str] = []
    if diversity_index < 0.45 or lineage_survival <= 1:
        governor_actions.append("increase_diversity_pressure")
    if domain_growth <= 1:
        governor_actions.append("spawn_exploration_quest")
    if float(memory_state.get("memory_growth", 0.0)) < 0.1:
        governor_actions.append("rebalance_resource_allocation")
    return {
        "diversity_index": diversity_index,
        "lineage_survival": lineage_survival,
        "policy_turnover": policy_turnover,
        "domain_growth": domain_growth,
        "memory_growth": round(float(memory_state.get("memory_growth", 0.0)), 4),
        "stable": stable,
        "governor_actions": governor_actions,
    }
