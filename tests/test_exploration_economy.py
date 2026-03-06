from metaos.runtime.exploration_economy import allocate_resources, exploration_economy


def test_exploration_economy_returns_budget_frame() -> None:
    out = exploration_economy(
        {
            "pressure": {"novelty_pressure": 0.8, "domain_shift_pressure": 0.5, "diversity_pressure": 0.6, "repair_pressure": 0.1, "efficiency_pressure": 0.2, "reframing_pressure": 0.1},
            "ecology": {"diversity_health": 0.3, "exploration_health": 0.4},
            "population": {
                "population_counts": {"policy": 1, "domain": 6},
                "growth_rates": {"policy": -0.1, "domain": 0.2},
                "extinction_risk": {"evaluation": 0.8},
            },
        }
    )
    assert set(out) == {"attention_budget", "mutation_budget", "selection_weights", "runtime_slot_allocation", "memory_pressure"}
    assert 0.0 <= out["attention_budget"] <= 1.0
    assert 0.0 <= out["mutation_budget"] <= 1.0
    assert out["runtime_slot_allocation"]["runtime_slots"] >= 3


def test_allocate_resources_returns_selection_and_slots() -> None:
    out = allocate_resources(
        {"novelty_pressure": 0.7, "diversity_pressure": 0.8, "efficiency_pressure": 0.2, "repair_pressure": 0.1, "domain_shift_pressure": 0.5, "reframing_pressure": 0.3},
        {"diversity_health": 0.4, "exploration_health": 0.35},
        {"population_counts": {"policy": 0}, "growth_rates": {"domain": -0.2}, "extinction_risk": {"evaluation": 0.7}},
    )
    assert "selection_weights" in out
    assert "domain_genome" in out["selection_weights"]
    assert out["runtime_slot_allocation"]["exploration_slots"] >= 1
