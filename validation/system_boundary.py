from __future__ import annotations

from typing import Any, Mapping


HUMAN_ONLY = {"constitution", "goal", "acceptance"}
SYSTEM_ONLY = {"exploration", "implementation", "validation", "evolution", "expansion"}


def validate_system_boundary(payload: Mapping[str, Any]) -> dict[str, Any]:
    human = {str(item) for item in payload.get("human", [])}
    system = {str(item) for item in payload.get("system", [])}
    return {
        "ok": human == HUMAN_ONLY and system == SYSTEM_ONLY,
        "human": sorted(human),
        "system": sorted(system),
        "expected_human": sorted(HUMAN_ONLY),
        "expected_system": sorted(SYSTEM_ONLY),
    }
