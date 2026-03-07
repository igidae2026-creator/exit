from __future__ import annotations

from typing import Any, Mapping

from validation.boundary import HUMAN_KEYS, SYSTEM_KEYS, validate_boundary


HUMAN_ONLY = HUMAN_KEYS
SYSTEM_ONLY = SYSTEM_KEYS


def validate_system_boundary(payload: Mapping[str, Any]) -> dict[str, Any]:
    boundary = validate_boundary(payload)
    human = {str(item) for item in payload.get("human", [])}
    system = {str(item) for item in payload.get("system", [])}
    overlap = sorted(human.intersection(system))
    human_missing = sorted(HUMAN_ONLY.difference(human))
    system_missing = sorted(SYSTEM_ONLY.difference(system))
    human_extra = sorted(human.difference(HUMAN_ONLY))
    system_extra = sorted(system.difference(SYSTEM_ONLY))
    return {
        "ok": boundary["ok"] and not overlap and not human_missing and not system_missing and not human_extra and not system_extra,
        "human": sorted(human),
        "system": sorted(system),
        "overlap": overlap,
        "human_missing": human_missing,
        "system_missing": system_missing,
        "human_extra": human_extra,
        "system_extra": system_extra,
        "expected_human": sorted(HUMAN_ONLY),
        "expected_system": sorted(SYSTEM_ONLY),
    }


__all__ = ["HUMAN_ONLY", "SYSTEM_ONLY", "validate_system_boundary"]
