from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


PRIMARY_ARTIFACT_CLASSES = {
    "output",
    "strategy",
    "quest",
    "policy",
    "evaluation",
    "repair",
    "domain",
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
    return {
        "artifact_id": artifact_id,
        "class": aclass,
        "type": atype,
        "schema_version": schema_version,
        "created_at": created_at,
        "immutable": bool(immutable),
        "spec": dict(spec or {}),
        "blobs": dict(blobs or {}),
        "refs": {
            "parents": list((refs or {}).get("parents", [])),
            "inputs": list((refs or {}).get("inputs", [])),
            "subjects": list((refs or {}).get("subjects", [])),
            "context": dict((refs or {}).get("context", {})),
        },
        "provenance": dict(provenance or {}),
        "constraints": dict(constraints or {}),
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

