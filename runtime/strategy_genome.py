from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping
import uuid


@dataclass(frozen=True)
class StrategyGenome:
    id: str
    domain: str
    eval_axes: dict[str, float] = field(default_factory=dict)
    mutation_ops: list[str] = field(default_factory=lambda: ["perturb", "swap", "recombine"])
    budget: float = 0.0
    parent: str | None = None

    @classmethod
    def create(
        cls,
        *,
        domain: str,
        eval_axes: Mapping[str, float] | None = None,
        mutation_ops: list[str] | None = None,
        budget: float = 0.0,
        parent: str | None = None,
        id: str | None = None,
    ) -> "StrategyGenome":
        return cls(
            id=id or uuid.uuid4().hex,
            domain=domain,
            eval_axes={key: float(value) for key, value in dict(eval_axes or {}).items()},
            mutation_ops=list(mutation_ops or ["perturb", "swap", "recombine"]),
            budget=float(budget),
            parent=parent,
        )

    def with_updates(self, **kwargs: Any) -> "StrategyGenome":
        data = self.to_dict()
        data.update(kwargs)
        return StrategyGenome.create(**data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "domain": self.domain,
            "eval_axes": dict(self.eval_axes),
            "mutation_ops": list(self.mutation_ops),
            "budget": self.budget,
            "parent": self.parent,
        }


@dataclass(frozen=True)
class DomainGenome:
    adapter: str
    constraints: dict[str, Any] = field(default_factory=dict)
    evaluation_recipe: dict[str, float] = field(default_factory=dict)
    mutation_priors: dict[str, float] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        adapter: str,
        constraints: Mapping[str, Any] | None = None,
        evaluation_recipe: Mapping[str, float] | None = None,
        mutation_priors: Mapping[str, float] | None = None,
    ) -> "DomainGenome":
        return cls(
            adapter=adapter,
            constraints=dict(constraints or {}),
            evaluation_recipe={key: float(value) for key, value in dict(evaluation_recipe or {}).items()},
            mutation_priors={key: float(value) for key, value in dict(mutation_priors or {}).items()},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter": self.adapter,
            "constraints": dict(self.constraints),
            "evaluation_recipe": dict(self.evaluation_recipe),
            "mutation_priors": dict(self.mutation_priors),
        }


def canonical_domain_genome() -> DomainGenome:
    return DomainGenome.create(
        adapter="code_domain",
        constraints={"canonical_only": False, "max_lineage_share": 0.68, "minimum_lineages": 2},
        evaluation_recipe={"quality": 0.22, "novelty": 0.14, "diversity": 0.12, "efficiency": 0.18, "usefulness": 0.16, "persistence": 0.08, "recombination": 0.10, "cost": -0.08},
        mutation_priors={"perturb": 0.45, "swap": 0.25, "recombine": 0.30},
    )


__all__ = ["DomainGenome", "StrategyGenome", "canonical_domain_genome"]
