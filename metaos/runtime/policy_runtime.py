from __future__ import annotations

from typing import Any, Mapping

from artifact.registry import load_envelope, register_envelope
from kernel.policy_runtime import bind as bind_bundle


def evolve_policy(
    policy: Mapping[str, Any],
    *,
    pressure: Mapping[str, float],
    tick: int,
    parent: str | None = None,
) -> dict[str, Any]:
    artifact_id = register_envelope(
        aclass="policy",
        atype="runtime_policy",
        spec={"policy": dict(policy), "tick": int(tick)},
        refs={"parents": [parent] if parent else [], "inputs": [], "subjects": [], "context": {}},
        provenance={
            "score": float(pressure.get("efficiency_pressure", 0.0)),
            "novelty": float(pressure.get("novelty_pressure", 0.0)),
            "diversity": float(pressure.get("diversity_pressure", 0.0)),
            "efficiency": 1.0 - float(pressure.get("efficiency_pressure", 0.0)),
        },
        constraints={"tick_boundary_only": True},
    )
    return {"artifact_id": artifact_id, "policy": dict(policy), "tick": int(tick)}


def swap_policy(bundle_id: str | None, tick: int) -> dict[str, Any]:
    frame = bind_bundle(bundle_id, tick)
    return {
        "tick": frame.tick,
        "bundle_id": frame.bundle_id,
        "bundle": dict(frame.bundle),
        "family_ids": dict(frame.family_ids),
    }


def load_policy_artifact(artifact_id: str) -> dict[str, Any]:
    envelope = load_envelope(artifact_id)
    if not envelope:
        return {}
    return {
        "artifact_id": str(envelope.get("artifact_id", "")),
        "artifact_type": str(envelope.get("artifact_type", "")),
        "payload": dict(envelope.get("payload", {})) if isinstance(envelope.get("payload"), Mapping) else {},
        "immutable": bool(envelope.get("immutable", True)),
    }


__all__ = ["evolve_policy", "load_policy_artifact", "swap_policy"]
