from __future__ import annotations

from typing import Any, Mapping

from artifact.registry import register_envelope
from metaos.runtime.domain_pool import register_domain


def discover_domains(civilization_memory: Mapping[str, Any], pressure: Mapping[str, Any]) -> list[str]:
    existing = set(
        (civilization_memory.get("domains", {}) if isinstance(civilization_memory.get("domains"), Mapping) else {}).keys()
    )
    existing.update(
        str(name)
        for name in (civilization_memory.get("domain_distribution", {}) if isinstance(civilization_memory.get("domain_distribution"), Mapping) else {}).keys()
    )
    if "selected_experiments" in pressure:
        selected = set(str(name) for name in pressure.get("selected_experiments", []))
        return sorted(selected - existing)

    pressure_state = dict(pressure.get("pressure", pressure)) if isinstance(pressure, Mapping) else {}
    novelty = float(pressure_state.get("novelty_pressure", 0.0))
    diversity = float(pressure_state.get("diversity_pressure", 0.0))
    domain_shift = float(pressure_state.get("domain_shift_pressure", 0.0))
    knowledge_density = float(civilization_memory.get("knowledge_density", 0.0))
    if max(novelty, domain_shift) < 0.55 and diversity < 0.65:
        return []

    seed = int(round(1000 * (novelty + domain_shift + knowledge_density)))
    name = f"civilization_domain_{len(existing) + 1}_{seed}"
    if name in existing:
        return []
    genome = {
        "name": name,
        "constraints": {
            "novelty": round(0.4 + 0.4 * novelty, 4),
            "diversity": round(0.3 + 0.4 * diversity, 4),
        },
        "mutation_priors": {"mutation_rate": round(0.18 + 0.22 * domain_shift, 4)},
    }
    register_domain(name, genome)
    register_envelope(
        aclass="domain",
        atype="domain_genome",
        spec={"genome": genome, "routing": {"selected_domain": name}},
        provenance={"novelty": novelty, "diversity": diversity, "score": knowledge_density},
    )
    return [name]


__all__ = ["discover_domains"]
