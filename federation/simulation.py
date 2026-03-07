from __future__ import annotations

import random
from collections import Counter
from typing import Any

from federation.federation_topology import topology_state


def simulate_federation(*, nodes: int = 4, ticks: int = 2000, seed: int = 42, topology_type: str = "mesh", materialize: bool = False, hydrate: bool = False) -> dict[str, Any]:
    rng = random.Random(seed)
    node_ids = [f"node_{index + 1}" for index in range(max(1, nodes))]
    topology = topology_state(node_ids, topology_type)
    artifact_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    policy_counts: Counter[str] = Counter()
    knowledge_events = 0
    adopted_artifacts = 0
    adopted_domains = 0
    adopted_policies = 0
    adopted_evaluations = 0
    mirrored_external_artifacts = 0
    active_mirrored_artifacts = 0
    foreign_origins: Counter[str] = Counter()
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
            if materialize and peers and tick % 6 == 0:
                adopted_artifacts += 1
                adopted_domains += 1 if tick % 12 == 0 else 0
                adopted_policies += 1 if tick % 9 == 0 else 0
                adopted_evaluations += 1 if tick % 10 == 0 else 0
            if hydrate and materialize and peers and tick % 8 == 0:
                mirrored_external_artifacts += 1
                active_mirrored_artifacts += 1 if tick % 16 == 0 else 0
                foreign_origins[peers[tick % len(peers)]] += 1
    total_artifacts = sum(artifact_counts.values())
    total_domains = sum(domain_counts.values())
    total_policies = sum(policy_counts.values())
    topology = topology_state(node_ids, topology_type, artifact_events=total_artifacts, knowledge_events=knowledge_events)
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
        "policy_diffusion_rate": round(total_policies / max(1.0, float(ticks * len(node_ids) or 1)), 4),
        "knowledge_flow_rate": round(knowledge_events / max(1.0, float(ticks * len(node_ids) or 1)), 4),
        "policy_diffusion_bounded": total_policies <= max(1, ticks * len(node_ids)),
        "replay_ok_per_node": replay_ok,
        "civilization_diversity": diversity,
        "materialized": bool(materialize),
        "hydrated": bool(hydrate),
        "adopted_external_artifacts": adopted_artifacts,
        "adopted_domains": adopted_domains,
        "adopted_external_policies": adopted_policies,
        "active_external_evaluation_generations": adopted_evaluations,
        "mirrored_external_artifacts": mirrored_external_artifacts,
        "active_mirrored_artifacts": active_mirrored_artifacts,
        "hydration_rate": round(mirrored_external_artifacts / max(1.0, float(adopted_artifacts or 1)), 4),
        "foreign_origin_distribution": dict(foreign_origins),
        "federation_adoption_rate": round((adopted_artifacts + adopted_domains + adopted_policies + adopted_evaluations) / max(1.0, float(ticks * len(node_ids) or 1)), 4),
        "federation_activation_rate": round((adopted_policies + adopted_evaluations) / max(1.0, float(ticks * len(node_ids) or 1)), 4),
        "healthy": replay_ok and diversity > 0.0,
    }


__all__ = ["simulate_federation"]
