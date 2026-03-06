from __future__ import annotations

from typing import Any, Mapping


def validate_constitution(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {"name": "constitution", "ok": "quota" not in set(payload.get("artifact_classes", []))}

