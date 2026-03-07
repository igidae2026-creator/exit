from __future__ import annotations

from typing import Any, Mapping

from artifact.registry import load_envelope, register_envelope
from federation.federation_exchange import diffuse_policy
from federation.federation_state import local_node_id
from genesis.policy_runtime import bind as bind_bundle


def evolve_policy(
    policy: Mapping[str, Any],
    *,
    pressure: Mapping[str, float],
    tick: int,
    parent: str | None = None,
) -> dict[str, Any]:
    current_policy = dict(policy)
    efficiency = float(pressure.get("efficiency_pressure", 0.0))
    novelty = float(pressure.get("novelty_pressure", 0.0))
    diversity = float(pressure.get("diversity_pressure", 0.0))
    turnover_quality = round(max(0.0, min(1.0, (0.45 * novelty) + (0.35 * diversity) + (0.20 * (1.0 - efficiency)))), 4)
    stagnation = round(max(0.0, min(1.0, 0.7 - turnover_quality)), 4)
    artifact_id = register_envelope(
        aclass="policy",
        atype="runtime_policy",
        spec={
            "policy": current_policy,
            "tick": int(tick),
            "generation_quality": turnover_quality,
            "policy_origin": local_node_id(),
            "policy_adoption_rate": round(max(0.0, min(1.0, diversity + novelty)), 4),
            "policy_diffusion_depth": 0 if parent is None else 1,
        },
        refs={"parents": [parent] if parent else [], "inputs": [], "subjects": [], "context": {}},
        provenance={
            "score": efficiency,
            "novelty": novelty,
            "diversity": diversity,
            "efficiency": 1.0 - efficiency,
        },
        constraints={"tick_boundary_only": True},
    )
    diffusion = diffuse_policy(
        artifact_id,
        current_policy,
        policy_origin=local_node_id(),
        adoption_rate=round(max(0.0, min(1.0, diversity + novelty)), 4),
        diffusion_depth=0 if parent is None else 1,
        adopted=bool(parent),
    )
    return {
        "artifact_id": artifact_id,
        "policy": current_policy,
        "tick": int(tick),
        "policy_turnover_quality": turnover_quality,
        "policy_stagnation": stagnation,
        "policy_origin": diffusion["policy_origin"],
        "policy_adoption_rate": diffusion["policy_adoption_rate"],
        "policy_diffusion_depth": diffusion["policy_diffusion_depth"],
    }


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
