from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CivilizationState:
    tick: int = 0
    domains: dict[str, dict] = field(default_factory=dict)
    memory: dict[str, list] = field(default_factory=lambda: {"domain_genomes": [], "policy_lineage": [], "strategy_lineage": [], "archive_summaries": [], "extinction_memory": [], "resurrection_seeds": []})
    lineage_counts: dict[str, int] = field(default_factory=dict)
    created_domains: list[str] = field(default_factory=list)
    active_domains: list[str] = field(default_factory=list)
    economy: dict[str, Any] = field(default_factory=dict)
    pressure: dict[str, float] = field(default_factory=dict)


__all__ = ["CivilizationState"]
