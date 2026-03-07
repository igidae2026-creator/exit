from __future__ import annotations

from typing import Any, Mapping, Sequence

from ecosystem.ecosystem_registry import register_node


def discover_nodes(nodes: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    discovered: list[dict[str, Any]] = []
    for row in nodes:
        node = {
            "node_id": str(row.get("node_id", "")).strip(),
            "node_domains": list(row.get("node_domains", [])),
            "node_capacity": int(row.get("node_capacity", 0) or 0),
            "node_artifact_rate": float(row.get("node_artifact_rate", 0.0) or 0.0),
            "node_specializations": list(row.get("node_specializations", [])),
            "active": bool(row.get("active", True)),
        }
        if node["node_id"]:
            discovered.append(register_node(node))
    return discovered


__all__ = ["discover_nodes"]
