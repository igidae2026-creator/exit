from __future__ import annotations

from typing import Any, Mapping


REQUIRED_ARTIFACT_FIELDS = (
    "artifact_id",
    "artifact_type",
    "lineage_id",
    "parent_ids",
    "domain",
    "policy_id",
    "strategy_id",
    "payload",
    "evaluation_vector",
    "fitness_vector",
    "creation_timestamp",
    "runtime_context",
    "provenance",
    "replay_checksum",
    "content_hash",
)


def validate_artifact_law(artifact: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(artifact)
    normalized = dict(payload)
    normalized.setdefault("artifact_type", normalized.get("type", ""))
    normalized.setdefault("lineage_id", normalized.get("artifact_id", ""))
    normalized.setdefault("domain", str((normalized.get("payload", {}) if isinstance(normalized.get("payload"), Mapping) else {}).get("domain", "unknown")))
    normalized.setdefault("policy_id", "")
    normalized.setdefault("strategy_id", "")
    normalized.setdefault("evaluation_vector", dict(normalized.get("score_vector", {})))
    normalized.setdefault("fitness_vector", {"quality": float((normalized.get("score_vector", {}) if isinstance(normalized.get("score_vector"), Mapping) else {}).get("score", 0.0) or 0.0)})
    normalized.setdefault("creation_timestamp", normalized.get("created_at"))
    normalized.setdefault("runtime_context", {})
    normalized.setdefault("provenance", {})
    normalized.setdefault("replay_checksum", "")
    normalized.setdefault("content_hash", "")
    missing: list[str] = []
    for field in REQUIRED_ARTIFACT_FIELDS:
        if field not in normalized:
            missing.append(field)
            continue
        if field in {"policy_id", "strategy_id"}:
            continue
        if normalized.get(field) in (None, ""):
            missing.append(field)
    immutable = bool(payload.get("immutable", True))
    parent_ids = normalized.get("parent_ids", [])
    evaluation_vector = normalized.get("evaluation_vector", {})
    fitness_vector = normalized.get("fitness_vector", {})
    provenance = normalized.get("provenance", {})
    replayable = bool(normalized.get("creation_timestamp")) and isinstance(normalized.get("payload"), Mapping)
    ok = (
        not missing
        and immutable
        and isinstance(parent_ids, list)
        and isinstance(evaluation_vector, Mapping)
        and isinstance(fitness_vector, Mapping)
        and isinstance(provenance, Mapping)
        and replayable
    )
    return {
        "name": "artifact_law",
        "ok": ok,
        "missing": missing,
        "immutable": immutable,
        "lineage_tracked": isinstance(parent_ids, list),
        "replayable": replayable,
        "provenance_present": isinstance(provenance, Mapping),
        "content_addressed": bool(normalized.get("content_hash")) and bool(normalized.get("replay_checksum")),
    }


__all__ = ["REQUIRED_ARTIFACT_FIELDS", "validate_artifact_law"]
