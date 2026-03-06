from __future__ import annotations

from typing import Any, Mapping, Sequence

from metaos.runtime.meta_exploration import meta_exploration as runtime_meta_exploration


def meta_exploration(
    civilization_memory: Mapping[str, Any],
    pressure: Mapping[str, float],
    history: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    ecology = {
        "exploration_health": max(0.0, 1.0 - float(pressure.get("novelty_pressure", 0.0)) * 0.5),
        "diversity_health": max(0.0, 1.0 - float(pressure.get("diversity_pressure", 0.0)) * 0.5),
        "novelty_health": max(0.0, 1.0 - float(pressure.get("reframing_pressure", 0.0)) * 0.5),
        "domain_count": len(dict(civilization_memory.get("domain_distribution", {}))) or 1,
    }
    population = {"population_counts": dict(civilization_memory.get("artifact_distribution", {}))}
    out = runtime_meta_exploration(history or [], ecology, population)
    out["domain_discovery_rules"] = {
        "spawn_threshold": round(0.45 + 0.35 * float(pressure.get("domain_shift_pressure", 0.0)), 4),
        "knowledge_density_weight": round(0.20 + 0.30 * float(civilization_memory.get("knowledge_density", 0.0)), 4),
    }
    return out


__all__ = ["meta_exploration"]
