from runtime.runtime_safety import runtime_safety


def test_runtime_safety_exposes_pressure_and_actions() -> None:
    out = runtime_safety()
    assert set(out) >= {"storage_pressure", "runtime_pressure", "archive_pressure", "safety_actions"}
