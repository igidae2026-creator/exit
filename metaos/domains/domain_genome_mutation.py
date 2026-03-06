from __future__ import annotations

import copy
import random
from typing import Any

from metaos.domains.domain_genome import DomainGenome


def _bounded_number(value: Any, step: float = 0.1, low: float = 0.0, high: float = 1.0) -> Any:
    if not isinstance(value, (int, float)):
        return value
    return round(max(low, min(high, float(value) + random.uniform(-step, step))), 4)


def _mutate_mapping(values: dict[str, Any], step: float = 0.1) -> dict[str, Any]:
    mutated = copy.deepcopy(values)
    for key, value in mutated.items():
        if isinstance(value, dict):
            mutated[key] = _mutate_mapping(value, step=step)
        else:
            mutated[key] = _bounded_number(value, step=step)
    return mutated


def mutate_domain_genome(genome: DomainGenome, step: float = 0.1) -> DomainGenome:
    return DomainGenome(
        name=genome.name,
        constraints=_mutate_mapping(dict(genome.constraints), step=step),
        evaluation_recipe=_mutate_mapping(dict(genome.evaluation_recipe), step=step),
        mutation_priors=_mutate_mapping(dict(genome.mutation_priors), step=step),
    )
