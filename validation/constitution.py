from __future__ import annotations

from typing import Any, Mapping

_REQUIRED_LOOP = ["signal", "generate", "evaluate", "select", "mutate", "archive", "repeat"]
from validation.boundary import validate_boundary


def validate_constitution(payload: Mapping[str, Any]) -> dict[str, Any]:
    artifact_classes = {str(item) for item in payload.get("artifact_classes", [])}
    loop = [str(item) for item in payload.get("loop", _REQUIRED_LOOP)]
    missing_loop = [stage for stage in _REQUIRED_LOOP if stage not in loop]
    return {
        "name": "constitution",
        "ok": ("quota" not in artifact_classes) and not missing_loop,
        "artifact_classes": sorted(artifact_classes),
        "forbidden_artifact_classes": ["quota"],
        "required_loop": list(_REQUIRED_LOOP),
        "provided_loop": loop,
        "missing_loop": missing_loop,
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
