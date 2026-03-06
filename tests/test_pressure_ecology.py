from metaos.runtime.pressure_ecology import stabilize_pressure


def test_pressure_ecology_smooths_and_damps_repair_loops() -> None:
    out = stabilize_pressure(
        {"novelty_pressure": 1.3, "repair_pressure": 0.9, "reframing_pressure": 0.9, "domain_shift_pressure": 0.8},
        history=[
            {"stabilized_pressure": {"novelty_pressure": 0.5, "repair_pressure": 0.7, "reframing_pressure": 0.5, "domain_shift_pressure": 0.4}, "guard": {"freeze_export": True, "downshift_workers": True}},
            {"stabilized_pressure": {"novelty_pressure": 0.55, "repair_pressure": 0.68, "reframing_pressure": 0.52, "domain_shift_pressure": 0.42}, "guard": {"freeze_export": True, "downshift_workers": True}},
        ],
        guard={"freeze_export": True, "downshift_workers": True, "force_meta": True},
    )
    assert out["novelty_pressure"] <= 0.63
    assert out["repair_pressure"] < 0.74
    assert out["reframing_pressure"] < 0.58
