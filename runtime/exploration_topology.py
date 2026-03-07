from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence


def exploration_topology(history: Sequence[Mapping[str, Any]] | None) -> dict[str, Any]:
    rows = list(history or [])
    connectivity: Counter[str] = Counter()
    edge_counts: Counter[tuple[str, str]] = Counter()
    cross_domain_events = 0
    total_events = 0

    for row in rows:
        domain = str(row.get("domain", "default"))
        routing = row.get("routing", {}) if isinstance(row.get("routing"), Mapping) else {}
        selected = str(routing.get("selected_domain", domain))
        connectivity[domain] += 1
        connectivity[selected] += 1
        edge_counts[(domain, selected)] += 1
        total_events += 1
        if selected != domain:
            cross_domain_events += 1

    total_connectivity = sum(connectivity.values()) or 1
    domain_connectivity = {
        name: round(count / total_connectivity, 4) for name, count in sorted(connectivity.items())
    }
    cross_domain_knowledge_flow = round(cross_domain_events / max(1, total_events), 4)
    return {
        "domain_connectivity": domain_connectivity,
        "cross_domain_knowledge_flow": cross_domain_knowledge_flow,
        "edge_count": sum(edge_counts.values()),
        "active_domains": sorted(domain_connectivity),
    }
