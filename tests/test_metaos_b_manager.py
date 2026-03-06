from metaos_b import schedule


def test_metaos_b_manager_schedules_a_units() -> None:
    out = schedule(
        {"novelty_pressure": 0.6, "diversity_pressure": 0.5, "efficiency_pressure": 0.2, "repair_pressure": 0.1, "domain_shift_pressure": 0.2, "reframing_pressure": 0.1},
        {"code": {"score": 0.9}, "research": {"score": 0.4}},
        {"exploration_health": 0.5},
        {"tick": 3},
    )
    assert out["selected_experiments"][0] == "code"
    assert "code" in out["runtime_slots"]
    assert "code" in out["exploration_budgets"]
