from __future__ import annotations

from typing import Any, Mapping

from metaos_c.civilization_memory import remember
from metaos_c.civilization_state import CivilizationState
from metaos_c.domain_discovery import discover_domains
from metaos_c.exploration_topology import build_topology
from metaos_c.strategy_generation import generate_strategies


def evolve_civilization(manager_output: Mapping[str, Any], state: CivilizationState | None = None) -> dict[str, Any]:
    state = state or CivilizationState()
    pressure = dict(manager_output.get("pressure", {})) if isinstance(manager_output.get("pressure"), Mapping) else {}
    economy = dict(manager_output.get("economy", {})) if isinstance(manager_output.get("economy"), Mapping) else {}
    discovery_signal: Mapping[str, Any] = manager_output if manager_output.get("selected_experiments") else pressure
    new_domains = discover_domains(
        {
            "domains": state.domains,
            "domain_distribution": {name: 1 for name in state.domains},
            "knowledge_density": float(manager_output.get("knowledge_density", 0.0)),
            "memory_growth": float(manager_output.get("memory_growth", 0.0)),
        },
        discovery_signal,
        economy=economy,
    )
    for domain in new_domains:
        state.domains[domain] = {"name": domain}
        state.lineage_counts.setdefault(domain, 0)
    strategies = generate_strategies(manager_output)
    state.memory = remember({"memory": state.memory}, {"selected_experiments": list(manager_output.get("selected_experiments", []))})
    state.memory["strategy_lineage"] = list(strategies["strategy_lineage"])
    state.tick += 1
    state.created_domains = sorted(state.domains)
    state.active_domains = sorted(state.domains)
    state.economy = economy
    state.pressure = pressure
    topology = build_topology(state.domains)
    return {
        "civilization_state": state,
        "new_domains": new_domains,
        "topology": topology,
        "memory": dict(state.memory),
    }


__all__ = ["evolve_civilization"]
