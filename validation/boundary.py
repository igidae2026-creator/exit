from __future__ import annotations

from typing import Any, Mapping


HUMAN_KEYS = {"goal", "essence", "constraints", "acceptance"}
SYSTEM_KEYS = {"exploration", "implementation", "validation", "evolution"}


def validate_boundary(payload: Mapping[str, Any]) -> dict[str, Any]:
    roles = dict(payload or {})
    human = set(str(item) for item in roles.get("human", []))
    system = set(str(item) for item in roles.get("system", []))
    human_ok = human == HUMAN_KEYS
    system_ok = system == SYSTEM_KEYS
    return {
        "ok": human_ok and system_ok,
        "human": sorted(human),
        "system": sorted(system),
        "expected_human": sorted(HUMAN_KEYS),
        "expected_system": sorted(SYSTEM_KEYS),
    }
