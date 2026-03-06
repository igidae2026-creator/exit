from kernel.supervisor import guarded_step


def test_failure_escalation_replay_restore_for_invalid_state() -> None:
    out = guarded_step(lambda state: state, {"workers": 0, "pressure": {}})
    assert out["mode"] == "safe_mode"


def test_failure_escalation_promotes_diversity_and_repair() -> None:
    def fail(_: dict[str, object]) -> dict[str, object]:
        raise RuntimeError("boom")

    out = guarded_step(
        fail,
        {"workers": 2, "pressure": {"diversity_pressure": 0.2}, "lineage_state": {"surviving_lineages": 1}, "repair": {"failed": True}},
    )
    restored = out["state"] if isinstance(out, dict) and out.get("mode") == "safe_mode" else out
    assert restored["pressure"]["diversity_pressure"] >= 0.85
    assert restored["quest"]["type"] == "repair"

