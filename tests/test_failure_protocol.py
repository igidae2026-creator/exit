from kernel.supervisor import guarded_step


def test_failure_protocol_plateau_promotes_reframing() -> None:
    def fail(_: dict[str, object]) -> dict[str, object]:
        raise RuntimeError("boom")

    out = guarded_step(fail, {"workers": 2, "pressure": {}, "plateau": True})
    restored = out["state"] if isinstance(out, dict) and out.get("mode") == "safe_mode" else out
    assert restored["quest"]["type"] == "reframing"


def test_failure_protocol_invalid_state_replays_restore() -> None:
    out = guarded_step(lambda state: state, {"workers": 0, "pressure": {}})
    assert out["mode"] == "safe_mode"
