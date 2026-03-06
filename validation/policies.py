from __future__ import annotations

from typing import Any, Mapping

from kernel.contracts import POLICY_FAMILIES


def validate_policy_bundle(payload: Mapping[str, Any]) -> dict[str, Any]:
    family_ids = dict(payload.get("family_ids", {}))
    return {"name": "policies", "ok": set(family_ids).issubset(set(POLICY_FAMILIES))}

