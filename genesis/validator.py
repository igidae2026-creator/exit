from __future__ import annotations

from typing import Any, Mapping

from validation.artifacts import validate_artifact_classes
from validation.constitution import validate_constitution
from validation.domains import validate_domain_contract
from validation.gates import validate_runtime_gates
from validation.policies import validate_policy_bundle


def validate_runtime(payload: Mapping[str, Any]) -> dict[str, Any]:
    checks = [
        validate_constitution(payload),
        validate_artifact_classes(payload),
        validate_policy_bundle(payload),
        validate_domain_contract(payload),
        validate_runtime_gates(payload),
    ]
    ok = all(bool(row.get("ok")) for row in checks)
    return {"ok": ok, "checks": checks}


__all__ = ["validate_runtime"]
