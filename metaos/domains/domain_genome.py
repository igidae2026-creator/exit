from __future__ import annotations

from typing import Any


class DomainGenome:
    def __init__(
        self,
        name: str = "default",
        constraints: dict[str, Any] | None = None,
        evaluation_recipe: dict[str, Any] | None = None,
        mutation_priors: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.constraints = constraints or {}
        self.evaluation_recipe = evaluation_recipe or {"score": 1.0}
        self.mutation_priors = mutation_priors or {"mutation_rate": 0.2}

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "constraints": self.constraints,
            "evaluation_recipe": self.evaluation_recipe,
            "mutation_priors": self.mutation_priors,
        }
