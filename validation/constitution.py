from __future__ import annotations

from typing import Any, Mapping

from validation.boundary import validate_boundary


REQUIRED_LOOP = ("signal", "generate", "evaluate", "select", "mutate", "archive", "repeat")
REQUIRED_PRESSURE_AXES = ("novelty", "diversity", "efficiency", "repair", "domain_shift", "reframing")
FORBIDDEN_ARTIFACT_CLASSES = {"quota"}


def validate_constitution(payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    data = dict(payload or {})
    artifact_classes = {str(item) for item in data.get("artifact_classes", [])}
    loop = [str(item) for item in data.get("loop", data.get("loop_stages", REQUIRED_LOOP))]
    missing_loop = [stage for stage in REQUIRED_LOOP if stage not in loop]
    pressures = {str(item) for item in data.get("pressure_axes", REQUIRED_PRESSURE_AXES)}
    missing_pressures = [axis for axis in REQUIRED_PRESSURE_AXES if axis not in pressures]
    forbidden_present = sorted(FORBIDDEN_ARTIFACT_CLASSES.intersection(artifact_classes))
    boundary = validate_boundary(
        {
            "human": data.get("human", ["goal", "essence", "constraints", "acceptance"]),
            "system": data.get("system", ["exploration", "implementation", "validation", "evolution", "expansion"]),
        }
    )
    return {
        "name": "constitution",
        "ok": boundary["ok"] and not missing_loop and not missing_pressures and not forbidden_present,
        "boundary": boundary,
        "artifact_classes": sorted(artifact_classes),
        "forbidden_artifact_classes": sorted(FORBIDDEN_ARTIFACT_CLASSES),
        "forbidden_present": forbidden_present,
        "required_loop": list(REQUIRED_LOOP),
        "provided_loop": loop,
        "missing_loop": missing_loop,
        "pressure_axes": sorted(pressures),
        "required_pressure_axes": list(REQUIRED_PRESSURE_AXES),
        "missing_pressure_axes": missing_pressures,
    }


__all__ = [
    "FORBIDDEN_ARTIFACT_CLASSES",
    "REQUIRED_LOOP",
    "REQUIRED_PRESSURE_AXES",
    "validate_constitution",
]
