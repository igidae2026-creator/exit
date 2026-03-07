from __future__ import annotations

from typing import Any, Mapping

from validation.boundary import validate_boundary


def validate_constitution(payload: Mapping[str, Any]) -> dict[str, Any]:
    artifact_classes = {str(item) for item in payload.get("artifact_classes", [])}
    boundary = validate_boundary(
        {
            "human": payload.get("human", ["goal", "essence", "constraints", "acceptance"]),
            "system": payload.get("system", ["exploration", "implementation", "validation", "evolution", "expansion"]),
        }
    )
    required_pressures = {"novelty", "diversity", "efficiency", "repair", "domain_shift", "reframing"}
    present_pressures = {str(item) for item in payload.get("pressure_axes", required_pressures)}
    return {
        "name": "constitution",
        "ok": boundary["ok"] and "quota" not in artifact_classes and required_pressures.issubset(present_pressures),
        "boundary": boundary,
        "pressure_axes": sorted(present_pressures),
    }
