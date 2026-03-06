from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class CivilizationState:
    tick: int = 0
    domains: dict[str, dict] = field(default_factory=dict)
    memory: dict[str, list] = field(default_factory=lambda: {"domain_genomes": [], "policy_lineage": [], "strategy_lineage": [], "archive_summaries": [], "extinction_memory": [], "resurrection_seeds": []})


__all__ = ["CivilizationState"]
