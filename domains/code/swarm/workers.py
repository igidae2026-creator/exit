from __future__ import annotations

from typing import Any, Mapping


def run_swarm(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    workers = max(1, int(dict(plan).get("workers", 1)))
    return [{"worker": index, "status": "ok"} for index in range(workers)]

