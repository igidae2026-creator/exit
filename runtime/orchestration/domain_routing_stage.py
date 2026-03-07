from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from domains.domain_crossbreed import crossbreed
from domains.domain_genome_mutation import mutate_domain_genome
from domains.domain_recombination import recombine
from runtime.domain_pool import get_domain
from runtime.domain_router import route


def _genome_dict(genome: Any) -> dict[str, Any]:
    if hasattr(genome, "as_dict") and callable(genome.as_dict):
        return dict(genome.as_dict())
    if hasattr(genome, "to_dict") and callable(genome.to_dict):
        return dict(genome.to_dict())
    if isinstance(genome, Mapping):
        return dict(genome)
    return DomainGenomeCompat(name=str(getattr(genome, "name", getattr(genome, "adapter", "default")))).as_dict()


@dataclass(slots=True)
class DomainGenomeCompat:
    name: str = "default"
    constraints: dict[str, Any] | None = None
    evaluation_recipe: dict[str, Any] | None = None
    mutation_priors: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "constraints": dict(self.constraints or {}),
            "evaluation_recipe": dict(self.evaluation_recipe or {"score": 1.0}),
            "mutation_priors": dict(self.mutation_priors or {"mutation_rate": 0.2}),
        }


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
    genome: Any | None,
    active_meta_quest: Mapping[str, Any] | None,
    routing: Mapping[str, Any],
    ecology: Mapping[str, Any],
) -> dict[str, Any]:
    if genome is not None:
        active_genome = genome
    else:
        active_genome = DomainGenomeCompat(name=domain)
    genome_state = _genome_dict(active_genome)
    if float(stabilized_pressure.get("domain_shift_pressure", 0.0)) > 0.70 or float(stabilized_pressure.get("reframing_pressure", 0.0)) > 0.70 or active_meta_quest is not None:
        if active_meta_quest is not None or float(stabilized_pressure.get("reframing_pressure", 0.0)) > 0.75:
            genome_state = recombine(genome_state, None, stabilized_pressure)
        else:
            active_genome = mutate_domain_genome(active_genome, step=0.08)
            genome_state = _genome_dict(active_genome)
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
