from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from artifact.registry import load_envelope, register_envelope
from federation.federation_exchange import diffuse_policy
from federation.federation_state import federation_state, local_node_id
from genesis.policy_runtime import bind as bind_bundle
from genesis.spine import append_event
from runtime.knowledge_system import knowledge_guidance


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
    federation = federation_state()
    external_policy_influence = min(0.15, 0.05 * float(federation.get("active_external_policies", 0)))
    turnover_quality = round(max(0.0, min(1.0, (0.45 * novelty) + (0.35 * diversity) + (0.20 * (1.0 - efficiency)) + external_policy_influence)), 4)
    stagnation = round(max(0.0, min(1.0, 0.7 - turnover_quality)), 4)
    digest = hashlib.sha256(json.dumps(current_policy, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()[:12]
    policy_id = f"policy:{tick}:{digest}"
    guidance = knowledge_guidance(domain=str(current_policy.get("domain", "policy")), pressure=dict(pressure))
    replacement_reason = "staleness_reduction" if stagnation >= 0.4 else "breakout_capture"
    evaluation_vector = {
        "turnover_quality": turnover_quality,
        "stagnation": stagnation,
        "reuse_bias": float(guidance.get("reuse_bias", 0.0)),
    }
    artifact_id = register_envelope(
        aclass="policy",
        atype="runtime_policy",
        spec={
            "policy": current_policy,
            "tick": int(tick),
            "policy_id": policy_id,
            "generation": int(tick),
            "parent_policy": str(parent or ""),
            "activation_tick": int(tick),
            "replacement_reason": replacement_reason,
            "evaluation_vector": evaluation_vector,
            "generation_quality": turnover_quality,
            "policy_origin": local_node_id(),
            "policy_adoption_rate": round(max(0.0, min(1.0, diversity + novelty)), 4),
            "policy_diffusion_depth": 0 if parent is None else 1,
            "policy_scope": "shared",
        },
        refs={"parents": [parent] if parent else [], "inputs": [], "subjects": [], "context": {}},
        provenance={
            "score": efficiency,
            "novelty": novelty,
            "diversity": diversity,
            "efficiency": 1.0 - efficiency,
            "repair": float(guidance.get("reuse_bias", 0.0)),
        },
        constraints={"tick_boundary_only": True, "policy_traceable": True},
    )
    diffusion = diffuse_policy(
        artifact_id,
        current_policy,
        policy_origin=local_node_id(),
        adoption_rate=round(max(0.0, min(1.0, diversity + novelty)), 4),
        diffusion_depth=0 if parent is None else 1,
        adopted=bool(parent),
    )
    append_event(
        "policy_evolved",
        {
            "artifact_id": artifact_id,
            "policy_id": policy_id,
            "generation": int(tick),
            "parent_policy": str(parent or ""),
            "activation_tick": int(tick),
            "replacement_reason": replacement_reason,
            "evaluation_vector": evaluation_vector,
        },
    )
    return {
        "artifact_id": artifact_id,
        "policy_id": policy_id,
        "policy": current_policy,
        "tick": int(tick),
        "generation": int(tick),
        "parent_policy": str(parent or ""),
        "activation_tick": int(tick),
        "replacement_reason": replacement_reason,
        "evaluation_vector": evaluation_vector,
        "policy_turnover_quality": turnover_quality,
        "policy_stagnation": stagnation,
        "policy_origin": diffusion["policy_origin"],
        "policy_adoption_rate": diffusion["policy_adoption_rate"],
        "policy_diffusion_depth": diffusion["policy_diffusion_depth"],
        "policy_scope": diffusion["policy_scope"],
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
        "policy_id": str((envelope.get("payload", {}) if isinstance(envelope.get("payload"), Mapping) else {}).get("policy_id", envelope.get("policy_id", ""))),
    }


__all__ = ["evolve_policy", "load_policy_artifact", "swap_policy"]
