from __future__ import annotations

from typing import Any, Mapping

from federation.federation_state import append_federation_row, federation_enabled, local_node_id


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
        "visibility": str(visibility),
        "origin_status": str(origin_status),
        "target_node": str(target_node or ""),
        "immutable": True,
    }
    if federation_enabled():
        append_federation_row("artifact_exchange", row)
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
        "accepted": bool(accepted),
    }
    if federation_enabled():
        append_federation_row("domain_propagation", row)
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
        "adopted": bool(adopted),
    }
    if federation_enabled():
        append_federation_row("policy_diffusion", row)
    return row


def exchange_knowledge(summary: Mapping[str, Any], *, source_node: str | None = None) -> dict[str, Any]:
    row = {
        "summary": dict(summary),
        "source_node": str(source_node or local_node_id()),
    }
    if federation_enabled():
        append_federation_row("knowledge_exchange", row)
    return row


__all__ = ["diffuse_policy", "exchange_knowledge", "export_artifact", "propagate_domain"]
