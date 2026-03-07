from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence


def knowledge_network_state(nodes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    sources: list[str] = []
    links: Counter[str] = Counter()
    flow = 0
    for node in nodes:
        node_id = str(node.get("node_id", "")).strip()
        if not node_id:
            continue
        sources.append(node_id)
        for peer in node.get("knowledge_links", []):
            link = f"{node_id}->{peer}"
            links[link] += 1
            flow += 1
    return {
        "knowledge_graph": {
            "knowledge_sources": sorted(dict.fromkeys(sources)),
            "knowledge_links": dict(links),
            "knowledge_flow": flow,
        }
    }


__all__ = ["knowledge_network_state"]
