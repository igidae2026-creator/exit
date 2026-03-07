from validation.genesis_invariants import validate_genesis_invariants


def _base_payload() -> dict:
    return {
        "artifact_classes": ["quest", "evaluation", "policy"],
        "loop_stages": ["signal", "generate", "evaluate", "select", "mutate", "archive", "repeat"],
        "runtime_gate": {"mode": "bounded", "max_ticks": 5, "tick_boundary_only": True, "allow_stop": True},
        "boundary": {
            "human": ["goal", "essence", "constraints", "acceptance"],
            "system": ["exploration", "implementation", "validation", "evolution", "expansion"],
        },
        "invariants": {
            "append_only_truth": True,
            "replayable_state": True,
            "artifact_immutability": True,
            "minimal_core": True,
            "domain_autonomy": True,
            "lineage_diversity": True,
        },
    }


def test_genesis_invariants_pass_for_canonical_payload() -> None:
    out = validate_genesis_invariants(_base_payload())
    assert out["ok"] is True
    assert out["violations"] == []


def test_genesis_invariants_fail_on_runtime_gate_and_loop_drift() -> None:
    payload = _base_payload()
    payload["runtime_gate"] = {"mode": "perpetual", "max_ticks": 2, "tick_boundary_only": False, "allow_stop": True}
    payload["loop_stages"] = ["signal", "evaluate", "select", "archive"]
    out = validate_genesis_invariants(payload)
    assert out["ok"] is False
    assert "runtime_gate_violation" in out["violations"]
    assert "constitution_violation" in out["violations"]
