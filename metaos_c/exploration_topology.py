from __future__ import annotations

from typing import Any, Mapping


def build_topology(domains: Mapping[str, Any]) -> dict[str, Any]:
    names = sorted(str(name) for name in domains)
    return {
        "domain_count": len(names),
        "edges": {name: [other for other in names if other != name] for name in names},
    }


__all__ = ["build_topology"]
