from runtime.exploration_economy import allocate_resources


def test_diversity_allocation_budget_rises_under_dominance() -> None:
    out = allocate_resources(
        {"novelty_pressure": 0.4, "diversity_pressure": 0.2, "efficiency_pressure": 0.1, "repair_pressure": 0.1, "domain_shift_pressure": 0.2, "reframing_pressure": 0.1},
        {"diversity_health": 0.2, "exploration_health": 0.4},
        {"population_counts": {"policy": 1}},
        civilization_state={"dominance_index": 0.9, "domain_population": {"default": 10}},
    )
    assert out["diversity_allocation_budget"] > 0
    assert "raise_diversity_budget" in out["rebalancing_actions"]

