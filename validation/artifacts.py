from __future__ import annotations

from typing import Any, Mapping

from kernel.contracts import PRIMARY_ARTIFACT_CLASSES


def validate_artifact_classes(payload: Mapping[str, Any]) -> dict[str, Any]:
    classes = set(payload.get("artifact_classes", PRIMARY_ARTIFACT_CLASSES))
    return {"name": "artifacts", "ok": classes.issubset(PRIMARY_ARTIFACT_CLASSES)}

