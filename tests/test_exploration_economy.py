from metaos.runtime.exploration_economy import exploration_economy


def test_exploration_economy_returns_budget_frame() -> None:
    out = exploration_economy(
        {
            "pressure": {"novelty_pressure": 0.8, "domain_shift_pressure": 0.5},
            "market": {"selection_bias": 0.2},
            "ecology": {"diversity_health": 0.3, "exploration_health": 0.4},
            "population": {
                "population_counts": {"policy": 1, "domain": 6},
                "growth_rates": {"policy": -0.1, "domain": 0.2},
                "extinction_risk": {"evaluation": 0.8},
            },
        }
    )
    assert set(out) == {"exploration_budget", "recombination_budget", "policy_budget", "evaluation_budget"}
    assert all(0.0 <= value <= 1.0 for value in out.values())

