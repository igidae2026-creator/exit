from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Mapping, Sequence


def domain_cluster_state(nodes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    clusters: dict[str, list[str]] = defaultdict(list)
    cluster_activity: Counter[str] = Counter()
    cluster_lineage_density: dict[str, float] = {}
    for node in nodes:
        domains = [str(name) for name in node.get("node_domains", [])]
        prefix = str(node.get("cluster", domains[0].split("_")[0] if domains else "general"))
        clusters[prefix].extend(domains)
        cluster_activity[prefix] += len(domains)
    for name, domains in clusters.items():
        cluster_lineage_density[name] = round(len(set(domains)) / max(1.0, float(len(domains))), 4)
    return {
        "domain_clusters": {name: sorted(set(domains)) for name, domains in clusters.items()},
        "cluster_domains": {name: sorted(set(domains)) for name, domains in clusters.items()},
        "cluster_activity": dict(cluster_activity),
        "cluster_lineage_density": cluster_lineage_density,
    }


__all__ = ["domain_cluster_state"]
