from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from artifact.archive import append_archive
from artifact.registry import register_mirrored_artifact, rows
from federation.federation_state import append_federation_row, local_node_id
from federation.hydration_policy import hydration_policy


def _hydration_state() -> dict[str, Any]:
    mirrored = [row for row in rows() if str(row.get("artifact_scope", "")) == "mirrored"]
    origins = Counter(str(row.get("origin_node", "")) for row in mirrored if row.get("origin_node"))
    depths = Counter(int(row.get("hydration_depth", 0) or 0) for row in mirrored)
    total_depth = sum(depths.values()) or 1
    return {
        "mirrored_external_artifacts": len(mirrored),
        "foreign_origin_distribution": dict(origins),
        "hydration_depth_distribution": {str(key): round(value / total_depth, 4) for key, value in sorted(depths.items())},
    }


def hydrate_artifact(
    artifact_id: str,
    *,
    origin_node: str,
    payload: Mapping[str, Any] | None = None,
    artifact_type: str = "artifact",
    artifact_class: str | None = None,
    adoption_chain: list[str] | None = None,
    hydration_depth: int = 1,
) -> dict[str, Any]:
    policy = hydration_policy(_hydration_state())
    if hydration_depth > int(policy.get("max_hydration_depth", 0)):
        return {"hydrated": False, "reason": "depth_limit"}
    if str(artifact_type) not in set(policy.get("artifact_type_allowlist", [])):
        return {"hydrated": False, "reason": "type_blocked"}
    if not bool(policy.get("allowed", True)):
        return {"hydrated": False, "reason": "origin_limit"}
    mirrored_rows = [row for row in rows() if str(row.get("artifact_scope", "")) == "mirrored"]
    if len(mirrored_rows) >= int(policy.get("max_hydrated_artifacts_per_window", 0)):
        return {"hydrated": False, "reason": "window_limit"}
    chain = list(adoption_chain or [str(origin_node), local_node_id()])
    mirrored_id = register_mirrored_artifact(
        source_artifact_id=str(artifact_id),
        source_node=str(origin_node),
        aclass=str(artifact_class or ("policy" if artifact_type == "policy" else "evaluation" if artifact_type == "evaluation" else "output")),
        atype=str(artifact_type),
        payload=dict(payload or {}),
        adoption_chain=chain,
        hydration_depth=int(hydration_depth),
    )
    append_archive(
        "mirrored_artifact",
        {
            "artifact_id": mirrored_id,
            "origin_artifact_id": str(artifact_id),
            "origin_node": str(origin_node),
            "adoption_chain": chain,
            "hydration_depth": int(hydration_depth),
        },
        visibility="external",
        origin_status="external",
        artifact_origin=str(origin_node),
        artifact_scope="mirrored",
        artifact_adoption_count=max(0, len(chain) - 1),
        artifact_propagation_depth=int(hydration_depth),
        origin_artifact_id=str(artifact_id),
        origin_node=str(origin_node),
        mirror_parent_ids=[str(artifact_id)],
        hydration_depth=int(hydration_depth),
        adoption_chain=chain,
    )
    append_federation_row(
        "artifact_hydration",
        {
            "artifact_id": mirrored_id,
            "origin_artifact_id": str(artifact_id),
            "origin_node": str(origin_node),
            "mirror_parent_ids": [str(artifact_id)],
            "adoption_chain": chain,
            "hydration_depth": int(hydration_depth),
            "hydrated": True,
        },
    )
    return {"hydrated": True, "artifact_id": mirrored_id}


def replay_hydrated_artifacts() -> list[dict[str, Any]]:
    hydrated: list[dict[str, Any]] = []
    for row in rows():
        if str(row.get("artifact_scope", "")) != "mirrored":
            continue
        payload = row.get("payload", {}) if isinstance(row.get("payload"), Mapping) else {}
        hydrated.append(
            {
                "artifact_id": str(row.get("artifact_id", "")),
                "origin_artifact_id": str(row.get("origin_artifact_id", "")),
                "origin_node": str(row.get("origin_node", "")),
                "mirror_parent_ids": list(row.get("mirror_parent_ids", [])),
                "adoption_chain": list(row.get("adoption_chain", [])),
                "hydration_depth": int(row.get("hydration_depth", 0) or 0),
                "active": str(payload.get("external_status", "")) == "activated",
            }
        )
    return hydrated


__all__ = ["hydrate_artifact", "replay_hydrated_artifacts"]
