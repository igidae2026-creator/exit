from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.autonomous_daemon import evaluate_strategy, mutate_strategy
from domains.code_domain import generate


@dataclass(slots=True)
class DomainGenome:
    adapter: str = "code_domain"
    constraints: dict[str, Any] = field(default_factory=lambda: {"canonical": True})
    evaluation_recipe: str = "core.autonomous_daemon.evaluate_strategy"
    mutation_priors: dict[str, float] = field(
        default_factory=lambda: {"quality": 0.2, "novelty": 0.25, "diversity": 0.2, "efficiency": 0.2, "cost": 0.15}
    )

    def generate(self) -> dict[str, float]:
        return generate()

    def mutate(self, strategy: dict[str, float]) -> dict[str, float]:
        return mutate_strategy(strategy)

    def evaluate(self, strategy: dict[str, float]) -> float:
        return float(evaluate_strategy(strategy))


def canonical_domain_genome() -> DomainGenome:
    return DomainGenome()
