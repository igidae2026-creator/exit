from metaos.runtime.pressure_market import market


def test_pressure_market_returns_bounded_normalized_biases() -> None:
    state = market(
        {
            "novelty_pressure": 0.8,
            "diversity_pressure": 0.6,
            "repair_pressure": 0.3,
            "efficiency_pressure": 0.2,
            "domain_shift_pressure": 0.4,
            "reframing_pressure": 0.1,
        }
    )
    assert set(state) == {"mutation_bias", "selection_bias", "archive_bias", "repair_bias", "domain_budget_bias"}
    assert all(0.0 <= value <= 1.0 for value in state.values())
    assert round(sum(state.values()), 6) == 1.0
