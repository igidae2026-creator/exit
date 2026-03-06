from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class DomainResources:
    runtime_slots: int
    memory_slots: int
    mutation_budget: float
    selection_budget: float


def load_resources(domain_runtime: Any) -> DomainResources:
    payload = domain_runtime.resources() if hasattr(domain_runtime, "resources") else {}
    data = dict(payload or {})
    return DomainResources(
        runtime_slots=int(data.get("runtime_slots", 1)),
        memory_slots=int(data.get("memory_slots", 1)),
        mutation_budget=float(data.get("mutation_budget", 0.0)),
        selection_budget=float(data.get("selection_budget", 0.0)),
    )


__all__ = ["DomainResources", "load_resources"]
