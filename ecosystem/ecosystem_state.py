from __future__ import annotations

from typing import Any

from ecosystem.artifact_market import artifact_market_state
from ecosystem.domain_clusters import domain_cluster_state
from ecosystem.ecosystem_registry import ecosystem_registry_state
from ecosystem.knowledge_network import knowledge_network_state


def ecosystem_state() -> dict[str, Any]:
    registry = ecosystem_registry_state()
    rows = list(registry.get("rows", []))
    clusters = domain_cluster_state(rows)
    market = artifact_market_state(rows)
    network = knowledge_network_state(rows)
    return {
        "registered_nodes": list(registry.get("registered_nodes", [])),
        "active_nodes": list(registry.get("active_nodes", [])),
        "domain_clusters": dict(clusters.get("domain_clusters", {})),
        "artifact_market": dict(market.get("artifact_market", {})),
        "knowledge_graph": dict(network.get("knowledge_graph", {})),
    }


__all__ = ["ecosystem_state"]
