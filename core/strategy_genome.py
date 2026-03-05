from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping
import uuid


@dataclass(frozen=True)
class StrategyGenome:
    """Represents a strategy configuration used by METAOS exploration."""

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
            eval_axes=dict(eval_axes or {}),
            mutation_ops=list(mutation_ops or ["perturb", "swap", "recombine"]),
            budget=float(budget),
            parent=parent,
        )

    def with_updates(self, **kwargs: Any) -> "StrategyGenome":
        data = self.to_dict()
        data.update(kwargs)
        return StrategyGenome(
            id=data["id"],
            domain=data["domain"],
            eval_axes=dict(data["eval_axes"]),
            mutation_ops=list(data["mutation_ops"]),
            budget=float(data["budget"]),
            parent=data["parent"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "domain": self.domain,
            "eval_axes": dict(self.eval_axes),
            "mutation_ops": list(self.mutation_ops),
            "budget": self.budget,
            "parent": self.parent,
        }


__all__ = ["StrategyGenome"]
