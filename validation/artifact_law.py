from __future__ import annotations

from typing import Any, Mapping


REQUIRED_ARTIFACT_FIELDS = (
    "artifact_id",
    "artifact_type",
    "parent_ids",
    "payload",
    "score_vector",
    "created_at",
)


def validate_artifact_law(artifact: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(artifact)
    missing = [field for field in REQUIRED_ARTIFACT_FIELDS if field not in payload]
    immutable = bool(payload.get("immutable", True))
    parent_ids = payload.get("parent_ids", [])
    score_vector = payload.get("score_vector", {})
    ok = (
        not missing
        and immutable
        and isinstance(parent_ids, list)
        and isinstance(score_vector, Mapping)
    )
    return {
        "name": "artifact_law",
        "ok": ok,
        "missing": missing,
        "immutable": immutable,
    }


__all__ = ["REQUIRED_ARTIFACT_FIELDS", "validate_artifact_law"]
