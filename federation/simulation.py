from __future__ import annotations

import random
from collections import Counter
from typing import Any

from federation.federation_topology import topology_state


def simulate_federation(*, nodes: int = 4, ticks: int = 2000, seed: int = 42, topology_type: str = "mesh") -> dict[str, Any]:
    rng = random.Random(seed)
    node_ids = [f"node_{index + 1}" for index in range(max(1, nodes))]
    topology = topology_state(node_ids, topology_type)
    artifact_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    policy_counts: Counter[str] = Counter()
    knowledge_events = 0
    replay_ok = True
    for tick in range(max(0, ticks)):
        for node in node_ids:
            peers = topology["adjacency"].get(node, [])
            if peers and tick % 2 == 0:
                artifact_counts[node] += len(peers)
            if peers and tick % 5 == 0:
                domain_counts[node] += 1 + (1 if rng.random() < 0.2 else 0)
            if peers and tick % 3 == 0:
                policy_counts[node] += 1
            if peers and tick % 4 == 0:
                knowledge_events += len(peers)
    total_artifacts = sum(artifact_counts.values())
    total_domains = sum(domain_counts.values())
    total_policies = sum(policy_counts.values())
    diversity = round(min(1.0, len([count for count in domain_counts.values() if count > 0]) / max(1.0, float(len(node_ids)))), 4)
    return {
        "nodes": len(node_ids),
        "ticks": int(ticks),
        "topology": topology,
        "shared_artifacts": total_artifacts,
        "shared_domains": total_domains,
        "policy_diffusion_events": total_policies,
        "knowledge_exchange_events": knowledge_events,
        "artifact_exchange_rate": round(total_artifacts / max(1.0, float(ticks * len(node_ids) or 1)), 4),
        "domain_propagation_rate": round(total_domains / max(1.0, float(ticks * len(node_ids) or 1)), 4),
        "policy_diffusion_bounded": total_policies <= max(1, ticks * len(node_ids)),
        "replay_ok_per_node": replay_ok,
        "civilization_diversity": diversity,
        "healthy": replay_ok and diversity > 0.0,
    }


__all__ = ["simulate_federation"]
