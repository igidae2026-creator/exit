from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence


def artifact_market_state(nodes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    supply: Counter[str] = Counter()
    demand: Counter[str] = Counter()
    for node in nodes:
        for artifact in node.get("artifacts", []):
            supply[str(artifact)] += 1
        for wanted in node.get("wanted_artifacts", []):
            demand[str(wanted)] += 1
    adoption = {}
    for artifact in set(supply) | set(demand):
        adoption[artifact] = round(min(1.0, supply[artifact] / max(1.0, float(demand[artifact] or 1))), 4)
    return {
        "artifact_market": {
            "artifact_supply": dict(supply),
            "artifact_demand": dict(demand),
            "artifact_adoption_rate": adoption,
        }
    }


__all__ = ["artifact_market_state"]
