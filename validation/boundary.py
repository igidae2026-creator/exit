from __future__ import annotations

from typing import Any, Mapping

HUMAN_KEYS = {"goal", "essence", "constraints", "acceptance"}
SYSTEM_KEYS = {"exploration", "implementation", "validation", "evolution", "expansion"}


def validate_boundary(payload: Mapping[str, Any]) -> dict[str, Any]:
    roles = dict(payload or {})
    human = {str(item) for item in roles.get("human", [])}
    system = {str(item) for item in roles.get("system", [])}
    overlap = sorted(human & system)
    system_ok = system == SYSTEM_KEYS or system == (SYSTEM_KEYS - {"expansion"})
    return {
        "ok": human == HUMAN_KEYS and system_ok and not overlap,
        "human": sorted(human),
        "system": sorted(system),
        "expected_human": sorted(HUMAN_KEYS),
        "expected_system": sorted(SYSTEM_KEYS),
        "role_overlap": overlap,
    }
