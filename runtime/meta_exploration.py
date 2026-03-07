from __future__ import annotations

from typing import Any, Mapping, Sequence

from runtime.domain_creation import domain_creation
from runtime.exploration_topology import exploration_topology


def _clamp(value: float, low: float = -0.12, high: float = 0.12) -> float:
    return round(max(low, min(high, float(value))), 4)


def _last_mapping(history: Sequence[Mapping[str, Any]], key: str) -> dict[str, Any]:
    for row in reversed(list(history)):
        value = row.get(key)
        if isinstance(value, Mapping):
            return dict(value)
    return {}


def _recent_domain_creation(history: Sequence[Mapping[str, Any]]) -> bool:
    recent = list(history)[-8:]
    for row in recent:
        meta = row.get("meta_exploration")
        if not isinstance(meta, Mapping):
            continue
        created = meta.get("domain_creation")
        if isinstance(created, Mapping) and created:
            return True
    return False


def meta_exploration(
    history: Sequence[Mapping[str, Any]] | None,
    ecology: Mapping[str, Any] | None,
    population: Mapping[str, Any] | None,
) -> dict[str, Any]:
    rows = list(history or [])
    ecology_state = dict(ecology or {})
    population_state = dict(population or {})
    topology = exploration_topology(rows)
    pressure = _last_mapping(rows, "stabilized_pressure") or _last_mapping(rows, "pressure")
    strategy = _last_mapping(rows, "strategy_of_strategy")

    knowledge_flow = float(topology.get("cross_domain_knowledge_flow", 0.0))
    domain_count = max(1, len(topology.get("active_domains", [])) or int(ecology_state.get("domain_count", 1) or 1))
    diversity_gap = 1.0 - float(ecology_state.get("diversity_health", 0.5))
    exploration_gap = 1.0 - float(ecology_state.get("exploration_health", 0.5))
    novelty_gap = 1.0 - float(ecology_state.get("novelty_health", 0.5))
    evaluation_count = float((population_state.get("population_counts", {}) if isinstance(population_state.get("population_counts"), Mapping) else {}).get("evaluation", 0))
    domain_count_population = float((population_state.get("population_counts", {}) if isinstance(population_state.get("population_counts"), Mapping) else {}).get("domain", 0))

    topology_mode = "stabilize"
    if domain_count <= 2 and max(diversity_gap, exploration_gap) >= 0.45:
        topology_mode = "expand"
    elif knowledge_flow < 0.22 and domain_count >= 2:
        topology_mode = "bridge"

    strategy_mutation = {
        "exploration_emphasis": _clamp(0.08 * exploration_gap + 0.05 * max(0.0, 0.25 - knowledge_flow)),
        "diversification_emphasis": _clamp(0.08 * diversity_gap + 0.03 * max(0.0, 0.35 - (domain_count / 6.0))),
        "reframing_emphasis": _clamp(0.04 * novelty_gap - 0.03 * knowledge_flow),
        "recombination_emphasis": _clamp(0.09 * max(0.0, 0.3 - knowledge_flow) + 0.04 * diversity_gap),
        "stabilization_emphasis": _clamp(0.05 * max(0.0, domain_count_population / max(1.0, evaluation_count + domain_count_population)) - 0.04 * exploration_gap),
    }
    evaluation_mutation = {
        "novelty": _clamp(0.07 * exploration_gap + 0.04 * max(0.0, 0.25 - knowledge_flow)),
        "diversity": _clamp(0.08 * diversity_gap),
        "score": _clamp(-0.05 * max(0.0, 0.3 - knowledge_flow)),
        "lineage_penalty": _clamp(0.04 * max(0.0, 0.2 - knowledge_flow)),
        "efficiency": _clamp(-0.03 * max(diversity_gap, exploration_gap)),
    }

    enriched_ecology = dict(ecology_state)
    enriched_ecology["knowledge_flow"] = round(knowledge_flow, 4)
    enriched_ecology["domain_count"] = domain_count
    new_domain = None if _recent_domain_creation(rows) else domain_creation(strategy or strategy_mutation, enriched_ecology, pressure)

    return {
        "strategy_mutation": strategy_mutation,
        "evaluation_mutation": evaluation_mutation,
        "domain_creation": new_domain,
        "topology_shift": {
            "mode": topology_mode,
            "domain_count": domain_count,
            "knowledge_flow": round(knowledge_flow, 4),
            "domain_connectivity": dict(topology.get("domain_connectivity", {})),
        },
    }
