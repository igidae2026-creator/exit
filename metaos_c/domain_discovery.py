from __future__ import annotations

from typing import Any, Mapping

from artifact.registry import register_envelope
from federation.federation_exchange import propagate_domain
from federation.federation_state import local_node_id
from runtime.domain_lifecycle import domain_lifecycle_state
from runtime.domain_expansion_policy import domain_expansion_policy
from runtime.domain_pool import domain_names, domain_snapshot, register_domain


def discover_domains(
    civilization_memory: Mapping[str, Any],
    pressure: Mapping[str, Any],
    economy: Mapping[str, Any] | None = None,
) -> list[str]:
    snapshot = domain_snapshot()
    existing = set(str(name) for name in snapshot.get("created_domains", []))
    existing.update((civilization_memory.get("domains", {}) if isinstance(civilization_memory.get("domains"), Mapping) else {}).keys())
    existing.update(str(name) for name in (civilization_memory.get("domain_distribution", {}) if isinstance(civilization_memory.get("domain_distribution"), Mapping) else {}).keys())
    existing.update(str(name) for name in (civilization_memory.get("inactive_domains", []) if isinstance(civilization_memory.get("inactive_domains"), list) else []))
    if "selected_experiments" in pressure:
        selected = set(str(name) for name in pressure.get("selected_experiments", []))
        return sorted(selected - existing)

    pressure_state = dict(pressure.get("pressure", pressure)) if isinstance(pressure, Mapping) else {}
    economy_state = dict(economy or {})
    novelty = float(pressure_state.get("novelty_pressure", 0.0))
    diversity = float(pressure_state.get("diversity_pressure", 0.0))
    domain_shift = float(pressure_state.get("domain_shift_pressure", 0.0))
    knowledge_density = float(civilization_memory.get("knowledge_density", 0.0))
    inferred_expansion_budget = int(economy_state.get("domain_expansion_budget", 0) or 0)
    if inferred_expansion_budget <= 0:
        inferred_expansion_budget = 1 if novelty + domain_shift + diversity >= 1.5 else 0
    policy = domain_expansion_policy(
        pressure_state,
        dict(civilization_memory),
        {"domain_count": len(existing) or len(domain_names()), "domain_expansion_budget": inferred_expansion_budget},
    )
    lifecycle = domain_lifecycle_state(dict(civilization_memory), pressure_state=pressure_state)
    if not policy["allowed"]:
        return []
    if int(lifecycle.get("resurrectable_domain_count", 0)) > 0:
        domain_name = str(list(lifecycle.get("resurrectable_domains", []))[0])
        register_domain(
            domain_name,
            {
                "name": domain_name,
                "domain_origin": local_node_id(),
                "domain_propagation_depth": 1,
                "domain_adoption_count": 1,
            },
        )
        propagate_domain(domain_name, domain_origin=local_node_id(), propagation_depth=1, adoption_count=1, accepted=True)
        return [domain_name]

    seed = int(round(1000 * (novelty + domain_shift + knowledge_density)))
    name = f"civilization_domain_{len(existing) + 1}_{seed}"
    if name in existing:
        return []
    genome = {
        "name": name,
        "domain_origin": local_node_id(),
        "domain_propagation_depth": 0,
        "domain_adoption_count": 1,
        "constraints": {
            "novelty": round(0.4 + 0.4 * novelty, 4),
            "diversity": round(0.3 + 0.4 * diversity, 4),
        },
        "mutation_priors": {"mutation_rate": round(0.18 + 0.22 * domain_shift, 4)},
        "lineage_branch_seed": f"{name}:root",
    }
    registered = register_domain(name, genome)
    register_envelope(
        aclass="domain",
        atype="domain_genome",
        spec={"genome": genome, "routing": {"selected_domain": name}, "domain": name},
        provenance={"novelty": novelty, "diversity": diversity, "score": knowledge_density},
        refs={"parents": [], "inputs": [], "subjects": [name], "context": {"expansion_policy": policy}},
    )
    propagate_domain(name, domain_origin=local_node_id(), propagation_depth=0, adoption_count=1, accepted=True)
    return [name]


def discover_domain_frame(
    civilization_memory: Mapping[str, Any],
    pressure: Mapping[str, Any],
    economy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    discovered = discover_domains(civilization_memory, pressure, economy=economy)
    inferred_expansion_budget = int((economy or {}).get("domain_expansion_budget", 0) or 0)
    if inferred_expansion_budget <= 0:
        inferred_expansion_budget = 1
    policy = domain_expansion_policy(
        pressure,
        civilization_memory,
        {
            "domain_count": len(domain_names()),
            "domain_expansion_budget": inferred_expansion_budget,
        },
    )
    return {
        "discovered_domains": list(discovered),
        "created_domains": list(discovered),
        "domain_lifecycle_state": domain_lifecycle_state(dict(civilization_memory), pressure_state=dict(pressure or {})),
        "expansion_pressure": float(policy["expansion_pressure"]),
        "branch_opportunity_score": float(policy.get("branch_opportunity_score", 0.0)),
        "domain_expansion_budget": inferred_expansion_budget,
        "target_domain_count": int(policy.get("target_domain_count", 0)),
        "expansion_decisions": list(policy["expansion_decisions"]),
    }


__all__ = ["discover_domain_frame", "discover_domains"]
