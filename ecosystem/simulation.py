from __future__ import annotations

import random
from typing import Any

from ecosystem.artifact_market import artifact_market_state
from ecosystem.domain_clusters import domain_cluster_state
from ecosystem.knowledge_network import knowledge_network_state


def simulate_ecosystem(*, nodes: int = 6, ticks: int = 3000, seed: int = 42) -> dict[str, Any]:
    rng = random.Random(seed)
    population = []
    for index in range(max(1, nodes)):
        node_id = f"ecosystem_node_{index + 1}"
        domains = [f"cluster{index % 3}_domain{j}" for j in range(1, 3)]
        artifacts = [f"artifact_{(index + j) % 4}" for j in range(2)]
        wanted = [f"artifact_{(index + j + 1) % 4}" for j in range(2)]
        links = [f"ecosystem_node_{((index + 1) % max(1, nodes)) + 1}"]
        population.append(
            {
                "node_id": node_id,
                "node_domains": domains,
                "node_capacity": 4 + index,
                "node_artifact_rate": round((ticks / max(1, nodes)) / 1000.0, 4),
                "node_specializations": [f"cluster{index % 3}"],
                "artifacts": artifacts,
                "wanted_artifacts": wanted,
                "knowledge_links": links,
                "active": True,
                "cluster": f"cluster{index % 3}",
            }
        )
    clusters = domain_cluster_state(population)
    market = artifact_market_state(population)["artifact_market"]
    network = knowledge_network_state(population)["knowledge_graph"]
    strategy_competition = {
        "strategy_origins": {row["node_id"]: len(row["node_domains"]) for row in population},
        "strategy_adoption": round(sum(market["artifact_adoption_rate"].values()) / max(1.0, float(len(market["artifact_adoption_rate"]) or 1)), 4),
        "strategy_survival_rate": round(min(1.0, len(population) / max(1.0, float(nodes))), 4),
    }
    return {
        "nodes": len(population),
        "ticks": int(ticks),
        "domain_clusters": clusters["domain_clusters"],
        "artifact_market_state": market,
        "knowledge_network_state": network,
        "strategy_competition": strategy_competition,
        "artifact_circulation": sum(market["artifact_supply"].values()),
        "knowledge_network_growth": int(network["knowledge_flow"]),
        "healthy": bool(population) and bool(clusters["domain_clusters"]) and strategy_competition["strategy_survival_rate"] > 0.0 and rng.random() >= 0.0,
    }


__all__ = ["simulate_ecosystem"]
