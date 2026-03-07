from __future__ import annotations

from typing import Any, Mapping

from artifact.registry import load_envelope
from genesis.contracts import BindingFrame, POLICY_FAMILIES


def _empty_bundle() -> dict[str, Any]:
    return {
        "type": "policy_bundle",
        "family_ids": {name: "" for name in POLICY_FAMILIES},
    }


def load_policy_bundle(bundle_id: str | None) -> dict[str, Any]:
    if not bundle_id:
        return _empty_bundle()
    envelope = load_envelope(bundle_id)
    if not envelope:
        return _empty_bundle()
    spec = dict(envelope.get("spec", {}))
    family_ids = dict(spec.get("family_ids", {}))
    for name in POLICY_FAMILIES:
        family_ids.setdefault(name, "")
    return {
        "artifact_id": bundle_id,
        "type": "policy_bundle",
        "family_ids": family_ids,
        "spec": spec,
    }


def bind(bundle_id: str | None, tick: int) -> BindingFrame:
    bundle = load_policy_bundle(bundle_id)
    return BindingFrame(
        tick=int(tick),
        bundle_id=str(bundle.get("artifact_id", bundle_id or "")),
        bundle=bundle,
        family_ids=dict(bundle.get("family_ids", {})),
    )

