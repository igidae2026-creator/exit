from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Iterable, Mapping

from artifact.store import get_body, put_body
from genesis.contracts import PRIMARY_ARTIFACT_CLASSES, artifact_envelope
from genesis.spine import append_jsonl
from validation.artifact_law import validate_artifact_law


DEFAULT_REGISTRY = ".metaos_runtime/data/artifact_registry.jsonl"


def _registry_path() -> Path:
    root = os.environ.get("METAOS_ROOT")
    if os.environ.get("METAOS_REGISTRY"):
        path = Path(os.environ["METAOS_REGISTRY"])
    elif root:
        path = Path(root) / "artifact_registry.jsonl"
    else:
        path = Path(DEFAULT_REGISTRY)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def register_envelope(
    *,
    aclass: str,
    atype: str,
    spec: Mapping[str, Any] | None = None,
    blobs: Mapping[str, Any] | None = None,
    refs: Mapping[str, Any] | None = None,
    provenance: Mapping[str, Any] | None = None,
    constraints: Mapping[str, Any] | None = None,
    artifact_id: str | None = None,
    created_at: float | None = None,
    immutable: bool = True,
) -> str:
    if aclass not in PRIMARY_ARTIFACT_CLASSES:
        raise ValueError(f"unsupported artifact class: {aclass}")
    artifact_id = artifact_id or str(uuid.uuid4())
    created_at = time.time() if created_at is None else float(created_at)
    envelope = artifact_envelope(
        artifact_id=artifact_id,
        aclass=aclass,
        atype=atype,
        spec=spec,
        blobs=blobs,
        schema_version="1.0",
        created_at=created_at,
        immutable=immutable,
        refs=refs,
        provenance=provenance,
        constraints=constraints,
    )
    body_ref = put_body(envelope["spec"], envelope["blobs"])
    row = {
        "artifact_id": artifact_id,
        "artifact_type": envelope["artifact_type"],
        "class": aclass,
        "type": atype,
        "lineage_id": envelope["lineage_id"],
        "parent_ids": list(envelope["parent_ids"]),
        "domain": envelope["domain"],
        "policy_id": envelope["policy_id"],
        "strategy_id": envelope["strategy_id"],
        "payload": dict(envelope["payload"]),
        "score_vector": dict(envelope["score_vector"]),
        "evaluation_vector": dict(envelope["evaluation_vector"]),
        "fitness_vector": dict(envelope["fitness_vector"]),
        "schema_version": envelope["schema_version"],
        "created_at": envelope["created_at"],
        "creation_timestamp": envelope["creation_timestamp"],
        "immutable": envelope["immutable"],
        "refs": envelope["refs"],
        "provenance": envelope["provenance"],
        "constraints": envelope["constraints"],
        "runtime_context": envelope["runtime_context"],
        "replay_checksum": envelope["replay_checksum"],
        "content_hash": envelope["content_hash"],
        "body_ref": body_ref,
    }
    validation = validate_artifact_law(row)
    if not validation["ok"]:
        raise ValueError(f"artifact law violation: {validation}")
    append_jsonl(_registry_path(), row)
    return artifact_id


def rows() -> list[dict[str, Any]]:
    path = _registry_path()
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                out.append(row)
    return out


def load_envelope(artifact_id: str) -> dict[str, Any] | None:
    for row in reversed(rows()):
        if str(row.get("artifact_id")) != str(artifact_id):
            continue
        body = get_body(str(row.get("body_ref", "")))
        return {
            **row,
            "spec": body["spec"],
            "blobs": body["blobs"],
            "artifact_type": row.get("artifact_type", row.get("type")),
            "lineage_id": row.get("lineage_id", row.get("artifact_id", "")),
            "parent_ids": list(row.get("parent_ids", ((row.get("refs") or {}).get("parents", [])))),
            "domain": row.get("domain", (body["spec"] if isinstance(body["spec"], Mapping) else {}).get("domain", "unknown")),
            "policy_id": row.get("policy_id", ""),
            "strategy_id": row.get("strategy_id", ""),
            "payload": dict(row.get("payload", body["spec"] if isinstance(body["spec"], Mapping) else {})),
            "score_vector": dict(row.get("score_vector", {})),
            "evaluation_vector": dict(row.get("evaluation_vector", row.get("score_vector", {}))),
            "fitness_vector": dict(row.get("fitness_vector", {})),
            "creation_timestamp": row.get("creation_timestamp", row.get("created_at")),
            "runtime_context": dict(row.get("runtime_context", {})) if isinstance(row.get("runtime_context"), Mapping) else {},
            "replay_checksum": str(row.get("replay_checksum", "")),
            "content_hash": str(row.get("content_hash", "")),
        }
    return None


def iter_by_class(aclass: str) -> Iterable[dict[str, Any]]:
    for row in rows():
        if str(row.get("class")) == str(aclass):
            yield row


def register_mirrored_artifact(
    *,
    source_artifact_id: str,
    source_node: str,
    aclass: str,
    atype: str,
    payload: Mapping[str, Any] | None = None,
    adoption_chain: list[str] | None = None,
    hydration_depth: int = 1,
) -> str:
    resolved_class = str(aclass if aclass in PRIMARY_ARTIFACT_CLASSES else "output")
    mirrored_payload = dict(payload or {})
    mirrored_payload.update(
        {
            "external_status": mirrored_payload.get("external_status", "mirrored"),
            "origin_node": str(source_node),
            "origin_artifact_id": str(source_artifact_id),
            "hydration_depth": int(hydration_depth),
            "adoption_chain": list(adoption_chain or [str(source_node)]),
        }
    )
    artifact_id = str(uuid.uuid4())
    created_at = time.time()
    body_ref = put_body(mirrored_payload, {})
    row = {
        "artifact_id": artifact_id,
        "artifact_type": str(atype),
        "class": resolved_class,
        "type": str(atype),
        "lineage_id": str(source_artifact_id),
        "parent_ids": [str(source_artifact_id)],
        "domain": str(mirrored_payload.get("domain", mirrored_payload.get("selected_domain", "unknown"))),
        "policy_id": str(mirrored_payload.get("policy_id", "")),
        "strategy_id": str(mirrored_payload.get("strategy_id", "")),
        "payload": mirrored_payload,
        "score_vector": {},
        "evaluation_vector": {},
        "fitness_vector": {},
        "schema_version": "1.0",
        "created_at": created_at,
        "creation_timestamp": created_at,
        "immutable": True,
        "refs": {"parents": [str(source_artifact_id)], "inputs": [], "subjects": [], "context": {}},
        "provenance": {
            "origin_node": str(source_node),
            "origin_artifact_id": str(source_artifact_id),
            "hydration_depth": int(hydration_depth),
            "adoption_chain": list(adoption_chain or [str(source_node)]),
        },
        "constraints": {"mirrored": True},
        "runtime_context": {"selected_domain": str(mirrored_payload.get("domain", "unknown"))},
        "replay_checksum": str(source_artifact_id),
        "content_hash": str(source_artifact_id),
        "body_ref": body_ref,
        "artifact_scope": "mirrored",
        "artifact_origin": str(source_node),
        "origin_node": str(source_node),
        "origin_artifact_id": str(source_artifact_id),
        "mirror_parent_ids": [str(source_artifact_id)],
        "hydration_depth": int(hydration_depth),
        "adoption_chain": list(adoption_chain or [str(source_node)]),
    }
    validation = validate_artifact_law(row)
    if not validation["ok"]:
        raise ValueError(f"artifact law violation: {validation}")
    append_jsonl(_registry_path(), row)
    return artifact_id
