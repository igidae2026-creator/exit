from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Mapping


PRIMARY_ARTIFACT_CLASSES = {
    "output",
    "strategy",
    "quest",
    "policy",
    "evaluation",
    "repair",
    "domain",
    "allocator",
}

POLICY_FAMILIES = (
    "selection_policy",
    "mutation_policy",
    "quest_policy",
    "evaluation_policy",
    "repair_policy",
    "quota_policy",
)


def artifact_refs() -> dict[str, list[str] | dict[str, Any]]:
    return {
        "parents": [],
        "inputs": [],
        "subjects": [],
        "context": {},
    }


def artifact_envelope(
    *,
    artifact_id: str,
    aclass: str,
    atype: str,
    spec: Mapping[str, Any] | None = None,
    blobs: Mapping[str, Any] | None = None,
    schema_version: str = "1.0",
    created_at: float | None = None,
    immutable: bool = True,
    refs: Mapping[str, Any] | None = None,
    provenance: Mapping[str, Any] | None = None,
    constraints: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if aclass not in PRIMARY_ARTIFACT_CLASSES:
        raise ValueError(f"unsupported artifact class: {aclass}")
    normalized_spec = dict(spec or {})
    normalized_refs = {
        "parents": list((refs or {}).get("parents", [])),
        "inputs": list((refs or {}).get("inputs", [])),
        "subjects": list((refs or {}).get("subjects", [])),
        "context": dict((refs or {}).get("context", {})),
    }
    score_vector = {
        "score": float((provenance or {}).get("score", 0.0) or 0.0),
        "novelty": float((provenance or {}).get("novelty", 0.0) or 0.0),
        "diversity": float((provenance or {}).get("diversity", 0.0) or 0.0),
        "efficiency": float((provenance or {}).get("efficiency", 0.0) or 0.0),
        "cost": float((provenance or {}).get("cost", 0.0) or 0.0),
    }
    evaluation_vector = {
        key: float((provenance or {}).get(key, score_vector.get(key, 0.0)) or 0.0)
        for key in ("score", "novelty", "diversity", "efficiency", "cost", "repair", "transfer")
    }
    fitness_vector = {
        "quality": score_vector["score"],
        "novelty": score_vector["novelty"],
        "diversity": score_vector["diversity"],
        "efficiency": score_vector["efficiency"],
        "resilience": float((provenance or {}).get("repair", 0.0) or 0.0),
    }
    domain = str(
        normalized_spec.get("domain")
        or normalized_spec.get("routing", {}).get("selected_domain")
        or normalized_refs["context"].get("domain")
        or "unknown"
    )
    runtime_context = {
        "tick": normalized_spec.get("tick", normalized_refs["context"].get("tick")),
        "goal": normalized_spec.get("goal", normalized_refs["context"].get("goal")),
        "selected_domain": domain,
        "quest_type": normalized_spec.get("quest", {}).get("type") if isinstance(normalized_spec.get("quest"), Mapping) else normalized_refs["context"].get("quest_type"),
    }
    content_hash = hashlib.sha256(
        json.dumps(normalized_spec, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    replay_checksum = hashlib.sha256(
        json.dumps(
            {
                "artifact_id": artifact_id,
                "class": aclass,
                "type": atype,
                "parent_ids": list(normalized_refs["parents"]),
                "payload": normalized_spec,
                "runtime_context": runtime_context,
            },
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    lineage_id = str(
        normalized_spec.get("lineage_id")
        or normalized_spec.get("metadata", {}).get("lineage_id")
        or normalized_refs["context"].get("lineage_id")
        or (list(normalized_refs["parents"])[0] if normalized_refs["parents"] else artifact_id)
    )
    policy_id = str(
        normalized_spec.get("policy_id")
        or normalized_spec.get("policy", {}).get("policy_id")
        or normalized_refs["context"].get("policy_id")
        or ""
    )
    strategy_id = str(
        normalized_spec.get("strategy_id")
        or normalized_spec.get("strategy", {}).get("strategy_id")
        or normalized_refs["context"].get("strategy_id")
        or ""
    )
    return {
        "artifact_id": artifact_id,
        "class": aclass,
        "type": atype,
        "artifact_type": atype,
        "lineage_id": lineage_id,
        "parent_ids": list(normalized_refs["parents"]),
        "domain": domain,
        "policy_id": policy_id,
        "strategy_id": strategy_id,
        "payload": normalized_spec,
        "score_vector": score_vector,
        "evaluation_vector": evaluation_vector,
        "fitness_vector": fitness_vector,
        "schema_version": schema_version,
        "created_at": created_at,
        "creation_timestamp": created_at,
        "immutable": bool(immutable),
        "spec": normalized_spec,
        "blobs": dict(blobs or {}),
        "refs": normalized_refs,
        "provenance": dict(provenance or {}),
        "constraints": dict(constraints or {}),
        "runtime_context": runtime_context,
        "content_hash": content_hash,
        "replay_checksum": replay_checksum,
    }


@dataclass(frozen=True, slots=True)
class BindingFrame:
    tick: int
    bundle_id: str
    bundle: Mapping[str, Any]
    family_ids: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class QuotaFrame:
    tick: int
    workers: int
    budgets: Mapping[str, float | int]
    phase: str = "run"


@dataclass(frozen=True, slots=True)
class DispatchFrame:
    tick: int
    phase: str
    quest_ids: tuple[str, ...] = ()
    policy_id: str | None = None
    parent_artifact_ids: tuple[str, ...] = ()
    quota_frame: QuotaFrame | None = None


@dataclass(frozen=True, slots=True)
class QuestSlots:
    continuity_slot: Mapping[str, Any] = field(default_factory=dict)
    frontier_slot: Mapping[str, Any] = field(default_factory=dict)
    escape_slot: Mapping[str, Any] = field(default_factory=dict)
