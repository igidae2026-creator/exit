from runtime.exploration_economy import allocate_resources


def test_economy_stabilization_exposes_balance_and_rebalancing() -> None:
    out = allocate_resources(
        {"novelty_pressure": 0.9, "diversity_pressure": 0.3, "efficiency_pressure": 0.2, "repair_pressure": 0.1, "domain_shift_pressure": 0.8, "reframing_pressure": 0.2},
        {"diversity_health": 0.4, "exploration_health": 0.3},
        {"population_counts": {"policy": 1}, "growth_rates": {"domain": 0.3}, "extinction_risk": {"evaluation": 0.2}},
    )
    assert 0.0 <= out["economy_balance_score"] <= 1.0
    assert 0.0 <= out["budget_skew"] <= 1.0
    assert "budget_mix" in out
    assert isinstance(out["rebalancing_actions"], list)
