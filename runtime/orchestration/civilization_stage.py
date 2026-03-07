from __future__ import annotations

from typing import Any, Mapping

from runtime.civilization_state import civilization_state as canonical_civilization_state
from runtime.civilization_stability import civilization_stability
from runtime.domain_pool import ensure_seed_domains


def civilization_snapshot(history: list[Mapping[str, Any]], population: Mapping[str, Any]) -> dict[str, Any]:
    population_counts = dict(population.get("population_counts", {})) if isinstance(population.get("population_counts"), Mapping) else {}
    lineages: dict[str, int] = {}
    for row in history[-64:]:
        routing = row.get("routing", {}) if isinstance(row.get("routing"), Mapping) else {}
        lineage_id = str(routing.get("selected_domain") or row.get("domain") or "default")
        lineages[lineage_id] = lineages.get(lineage_id, 0) + 1
    domains = {name: 1 for name in ensure_seed_domains()}
    policy_generations = sum(1 for row in history if isinstance(row.get("policy"), Mapping))
    memory_volume = sum(1 for row in history if row.get("meta_exploration") or row.get("quest"))
    return {
        "artifact_counts": {
            "artifact": sum(int(value) for value in population_counts.values()),
            "strategy": int(population_counts.get("strategy", 0)),
            "policy": int(population_counts.get("policy", 0)),
            "quest": len(history),
            "evaluation": int(population_counts.get("evaluation", 0)),
            "allocator": 1,
            "domain_genome": int(population_counts.get("domain", 0)),
            "memory": memory_volume,
        },
        "lineage_counts": lineages,
        "domain_counts": domains,
        "policy_generations": policy_generations,
        "memory_volume": memory_volume,
    }


def memory_pressure_snapshot(history: list[Mapping[str, Any]]) -> dict[str, float]:
    recent = history[-64:]
    kinds = 0
    for row in recent:
        kinds += sum(1 for key in ("quest", "policy", "meta_exploration", "routing", "repair") if row.get(key))
    memory_growth = min(1.0, len(recent) / 64.0)
    knowledge_density = min(1.0, kinds / max(1, len(recent) * 5))
    archive_pressure = min(1.0, (len(recent) + kinds) / 96.0)
    return {
        "memory_growth": round(memory_growth, 4),
        "knowledge_density": round(knowledge_density, 4),
        "archive_pressure": round(archive_pressure, 4),
    }


def build_civilization_frame(history: list[Mapping[str, Any]], population: Mapping[str, Any], ecology: Mapping[str, Any]) -> dict[str, Any]:
    civilization = civilization_snapshot(history, population)
    memory_state = memory_pressure_snapshot(history)
    stability = civilization_stability(ecology, civilization, memory_state)
    canonical = canonical_civilization_state(
        state={"knowledge_density": memory_state["knowledge_density"], "memory_growth": memory_state["memory_growth"]},
        history=history,
    )
    return {
        "civilization_state": {**civilization, **canonical},
        "memory_state": memory_state,
        "civilization_stability": stability,
    }


__all__ = ["build_civilization_frame", "civilization_snapshot", "memory_pressure_snapshot"]
