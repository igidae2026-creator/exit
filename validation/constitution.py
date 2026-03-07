from __future__ import annotations

from typing import Any, Mapping

_REQUIRED_LOOP = ["signal", "generate", "evaluate", "select", "mutate", "archive", "repeat"]


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
    }
