from __future__ import annotations

from typing import Any, Mapping

from federation.federation_state import append_federation_row, local_node_id
from federation.federation_transport import enqueue_transport


def _record(kind: str, identifier: str, status: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    row = {
        "id": str(identifier),
        "status": str(status),
        "origin_node": str(payload.get("origin_node", local_node_id())),
        "payload": dict(payload),
    }
    enqueue_transport("adoption", {"kind": kind, "id": identifier, "status": status})
    append_federation_row(f"{kind}_adoption", row)
    return row


def materialize_artifact(artifact_id: str, status: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return _record("artifact", artifact_id, status, dict(payload or {}))


def materialize_domain(domain: str, status: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return _record("domain", domain, status, dict(payload or {}))


def materialize_policy(policy_id: str, status: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return _record("policy", policy_id, status, dict(payload or {}))


def materialize_evaluation(evaluation_id: str, status: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return _record("evaluation", evaluation_id, status, dict(payload or {}))


__all__ = [
    "materialize_artifact",
    "materialize_domain",
    "materialize_evaluation",
    "materialize_policy",
]
