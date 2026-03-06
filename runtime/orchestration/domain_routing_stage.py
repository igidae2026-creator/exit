from __future__ import annotations

from typing import Any, Mapping

from metaos.domains.domain_crossbreed import crossbreed
from metaos.domains.domain_genome import DomainGenome
from metaos.domains.domain_genome_mutation import mutate_domain_genome
from metaos.domains.domain_recombination import recombine
from metaos.runtime.domain_router import route
from metaos.runtime.domain_pool import get_domain


def build_routing_frame(
    stabilized_pressure: Mapping[str, float],
    budgets: Mapping[str, Any],
    *,
    domain: str,
    guard: Mapping[str, Any],
    ecology: Mapping[str, Any],
    civilization_selection: Mapping[str, Any],
    history: list[Mapping[str, Any]],
) -> dict[str, Any]:
    routing = route(stabilized_pressure, budgets, domain=domain, guard=guard, ecology=ecology, civilization_selection=civilization_selection, history=history)
    if guard.get("force_reframing"):
        routing["stagnation_escape"] = True
    return {"routing": routing}


def evolve_domain_genome(
    stabilized_pressure: Mapping[str, float],
    *,
    domain: str,
    genome: DomainGenome | None,
    active_meta_quest: Mapping[str, Any] | None,
    routing: Mapping[str, Any],
    ecology: Mapping[str, Any],
) -> dict[str, Any]:
    active_genome = genome or DomainGenome(name=domain)
    genome_state = active_genome.as_dict()
    if float(stabilized_pressure.get("domain_shift_pressure", 0.0)) > 0.70 or float(stabilized_pressure.get("reframing_pressure", 0.0)) > 0.70 or active_meta_quest is not None:
        if active_meta_quest is not None or float(stabilized_pressure.get("reframing_pressure", 0.0)) > 0.75:
            genome_state = recombine(genome_state, None, stabilized_pressure)
        else:
            active_genome = mutate_domain_genome(active_genome, step=0.08)
            genome_state = active_genome.as_dict()
    crossbred = None
    if str((active_meta_quest or {}).get("type", "")) in {"reframing", "meta"} or float(ecology.get("diversity_health", 1.0)) < 0.45:
        selected_domain_name = str(routing.get("selected_domain", domain))
        selected_domain = get_domain(selected_domain_name) or {"name": selected_domain_name, "genome": genome_state}
        secondary = None
        if selected_domain_name != str(domain):
            secondary = get_domain(str(domain))
        crossbred = crossbreed(
            dict(selected_domain.get("genome") or genome_state),
            dict(secondary.get("genome")) if secondary and isinstance(secondary.get("genome"), Mapping) else None,
            stabilized_pressure,
        )
        genome_state = crossbred
    return {"genome": genome_state, "crossbred_genome": crossbred}


__all__ = ["build_routing_frame", "evolve_domain_genome"]
