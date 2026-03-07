from __future__ import annotations

from typing import Any


def _neighbors(nodes: list[str], topology_type: str) -> dict[str, list[str]]:
    names = list(nodes)
    if topology_type == "hub" and names:
        hub = names[0]
        return {name: ([peer for peer in names if peer != name] if name == hub else [hub]) for name in names}
    if topology_type == "ring" and len(names) > 1:
        return {
            name: [names[(index - 1) % len(names)], names[(index + 1) % len(names)]]
            for index, name in enumerate(names)
        }
    if topology_type == "mesh":
        return {name: [peer for peer in names if peer != name] for name in names}
    return {name: [names[(index + 1) % len(names)]] if len(names) > 1 else [] for index, name in enumerate(names)}


def topology_state(nodes: list[str], topology_type: str, *, artifact_events: int = 0, knowledge_events: int = 0) -> dict[str, Any]:
    adjacency = _neighbors(nodes, topology_type)
    node_degree = {node: len(peers) for node, peers in adjacency.items()}
    node_count = max(1.0, float(len(nodes) or 1))
    return {
        "topology_type": str(topology_type),
        "adjacency": adjacency,
        "node_degree": node_degree,
        "artifact_flow_rate": round(float(artifact_events) / node_count, 4),
        "knowledge_flow_rate": round(float(knowledge_events) / node_count, 4),
    }


__all__ = ["topology_state"]
