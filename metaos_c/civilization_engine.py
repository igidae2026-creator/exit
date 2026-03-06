from __future__ import annotations

from typing import Any, Mapping

from metaos_c.civilization_memory import remember
from metaos_c.civilization_state import CivilizationState
from metaos_c.domain_discovery import discover_domains
from metaos_c.exploration_topology import build_topology
from metaos_c.strategy_generation import generate_strategies


def evolve_civilization(manager_output: Mapping[str, Any], state: CivilizationState | None = None) -> dict[str, Any]:
    state = state or CivilizationState()
    new_domains = discover_domains({"domains": state.domains}, manager_output)
    for domain in new_domains:
        state.domains[domain] = {"name": domain}
    strategies = generate_strategies(manager_output)
    state.memory = remember({"memory": state.memory}, {"selected_experiments": list(manager_output.get("selected_experiments", []))})
    state.memory["strategy_lineage"] = list(strategies["strategy_lineage"])
    topology = build_topology(state.domains)
    return {
        "civilization_state": state,
        "new_domains": new_domains,
        "topology": topology,
        "memory": dict(state.memory),
    }


__all__ = ["evolve_civilization"]
