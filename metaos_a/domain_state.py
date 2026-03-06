from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DomainState:
    goal: str
    domain_name: str
    tick: int = 0
    artifact_ids: list[str] = field(default_factory=list)
    lineage_counts: dict[str, int] = field(default_factory=dict)
    last_metrics: dict[str, float] = field(default_factory=dict)
    last_output: dict[str, Any] = field(default_factory=dict)


__all__ = ["DomainState"]
