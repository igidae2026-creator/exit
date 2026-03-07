from __future__ import annotations

from typing import Any, Mapping

from federation.federation_adoption import materialize_artifact, materialize_domain, materialize_evaluation, materialize_policy
from federation.federation_hydration import hydrate_artifact
from federation.federation_state import append_federation_row, federation_enabled, local_node_id
from federation.federation_transport import enqueue_transport


def export_artifact(
    artifact_id: str,
    payload: Mapping[str, Any],
    *,
    visibility: str = "shared",
    origin_status: str = "local",
    target_node: str | None = None,
) -> dict[str, Any]:
    row = {
        "artifact_id": str(artifact_id),
        "payload": dict(payload),
        "artifact_origin": str(local_node_id()),
        "artifact_scope": str(visibility),
        "artifact_adoption_count": max(0, int(dict(payload).get("artifact_adoption_count", 0) or 0)),
        "artifact_propagation_depth": max(0, int(dict(payload).get("artifact_propagation_depth", 0) or 0)),
        "visibility": str(visibility),
        "origin_status": str(origin_status),
        "target_node": str(target_node or ""),
        "adoption_history": list(dict(payload).get("adoption_history", [])) if isinstance(dict(payload).get("adoption_history", []), list) else [],
        "immutable": True,
    }
    if federation_enabled():
        enqueue_transport("send", {"kind": "artifact", "artifact_id": artifact_id})
        enqueue_transport("receive", {"kind": "artifact", "artifact_id": artifact_id, "target_node": target_node or ""})
        append_federation_row("artifact_exchange", row)
        materialize_artifact(artifact_id, "observed", {"origin_node": row["artifact_origin"], **row})
        if str(origin_status) == "external":
            materialize_artifact(artifact_id, "imported", {"origin_node": row["artifact_origin"], **row})
            materialize_artifact(artifact_id, "adopted", {"origin_node": row["artifact_origin"], **row})
            hydrate_artifact(
                artifact_id,
                origin_node=str(row["artifact_origin"]),
                payload=dict(payload),
                artifact_type=str(dict(payload).get("artifact_type", "artifact") or "artifact"),
                artifact_class=str(dict(payload).get("class", "output") or "output"),
                adoption_chain=[str(row["artifact_origin"]), local_node_id()],
                hydration_depth=int(row.get("artifact_propagation_depth", 0) or 0) + 1,
            )
    return row


def propagate_domain(
    domain: str,
    *,
    domain_origin: str | None = None,
    propagation_depth: int = 0,
    adoption_count: int = 0,
    accepted: bool = True,
) -> dict[str, Any]:
    row = {
        "domain": str(domain),
        "domain_origin": str(domain_origin or local_node_id()),
        "domain_propagation_depth": max(0, int(propagation_depth)),
        "domain_adoption_count": max(0, int(adoption_count) + int(bool(accepted))),
        "domain_scope": "shared",
        "accepted": bool(accepted),
    }
    if federation_enabled():
        enqueue_transport("send", {"kind": "domain", "domain": domain})
        enqueue_transport("receive", {"kind": "domain", "domain": domain})
        append_federation_row("domain_propagation", row)
        materialize_domain(domain, "observed", {"origin_node": row["domain_origin"], **row})
    return row


def diffuse_policy(
    artifact_id: str,
    policy: Mapping[str, Any],
    *,
    policy_origin: str | None = None,
    adoption_rate: float = 0.0,
    diffusion_depth: int = 0,
    adopted: bool = False,
) -> dict[str, Any]:
    row = {
        "artifact_id": str(artifact_id),
        "policy": dict(policy),
        "policy_origin": str(policy_origin or local_node_id()),
        "policy_adoption_rate": round(max(0.0, min(1.0, float(adoption_rate))), 4),
        "policy_diffusion_depth": max(0, int(diffusion_depth)),
        "policy_scope": "shared",
        "adopted": bool(adopted),
    }
    if federation_enabled():
        enqueue_transport("send", {"kind": "policy", "artifact_id": artifact_id})
        enqueue_transport("receive", {"kind": "policy", "artifact_id": artifact_id})
        append_federation_row("policy_diffusion", row)
        materialize_policy(artifact_id, "observed", {"origin_node": row["policy_origin"], **row})
    return row


def exchange_knowledge(summary: Mapping[str, Any], *, source_node: str | None = None) -> dict[str, Any]:
    row = {
        "summary": dict(summary),
        "source_node": str(source_node or local_node_id()),
    }
    if federation_enabled():
        enqueue_transport("send", {"kind": "knowledge", "source_node": row["source_node"]})
        enqueue_transport("receive", {"kind": "knowledge", "source_node": row["source_node"]})
        append_federation_row("knowledge_exchange", row)
    return row


def import_evaluation(evaluation_id: str, evaluation: Mapping[str, Any], *, origin_node: str | None = None) -> dict[str, Any]:
    row = {
        "evaluation_id": str(evaluation_id),
        "evaluation": dict(evaluation),
        "origin_node": str(origin_node or local_node_id()),
    }
    if federation_enabled():
        enqueue_transport("send", {"kind": "evaluation", "evaluation_id": evaluation_id})
        enqueue_transport("receive", {"kind": "evaluation", "evaluation_id": evaluation_id})
        append_federation_row("evaluation_exchange", row)
        materialize_evaluation(evaluation_id, "observed", row)
    return row


__all__ = ["diffuse_policy", "exchange_knowledge", "export_artifact", "import_evaluation", "propagate_domain"]
