from __future__ import annotations

from typing import Any, Mapping

from validation.constitution import validate_constitution
from validation.gates import validate_runtime_gates
from validation.system_boundary import validate_system_boundary


REQUIRED_INVARIANTS = (
    "append_only_truth",
    "replayable_state",
    "artifact_immutability",
    "minimal_core",
    "domain_autonomy",
    "lineage_diversity",
)


def validate_genesis_invariants(payload: Mapping[str, Any]) -> dict[str, Any]:
    constitution = validate_constitution(
        {
            "artifact_classes": payload.get("artifact_classes", []),
            "loop": payload.get("loop_stages", []),
        }
    )
    gates = validate_runtime_gates(payload.get("runtime_gate", {}))
    boundary = validate_system_boundary(payload.get("boundary", {}))

    invariants = payload.get("invariants", {})
    missing = [name for name in REQUIRED_INVARIANTS if not bool(invariants.get(name, False))]

    violations: list[str] = []
    if not constitution["ok"]:
        violations.append("constitution_violation")
    if not gates["ok"]:
        violations.append("runtime_gate_violation")
    if not boundary["ok"]:
        violations.append("boundary_violation")
    if missing:
        violations.append("missing_invariants")

    return {
        "ok": not violations,
        "violations": violations,
        "missing_invariants": missing,
        "required_invariants": list(REQUIRED_INVARIANTS),
        "constitution": constitution,
        "runtime_gate": gates,
        "boundary": boundary,
    }
