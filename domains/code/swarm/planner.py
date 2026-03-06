from __future__ import annotations

from typing import Any, Mapping


def plan_swarm(quota: Mapping[str, Any], bindings: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "workers": int(dict(quota).get("workers", 1)),
        "binding_count": len(dict(bindings)),
        "mode": "bounded",
    }

