from __future__ import annotations

from typing import Any, Mapping


def tick_phase(previous: Mapping[str, Any] | None = None) -> dict[str, Any]:
    previous = dict(previous or {})
    tick = int(previous.get("tick", 0)) + 1
    return {
        "tick": tick,
        "phase": "tick_boundary",
        "previous_phase": str(previous.get("phase", "boot")),
    }

