from metaos.runtime.resource_allocator import allocate


def test_resource_allocator_returns_canonical_runtime_outputs() -> None:
    out = allocate(
        {
            "novelty_pressure": 0.7,
            "diversity_pressure": 0.6,
            "efficiency_pressure": 0.2,
            "repair_pressure": 0.1,
            "domain_shift_pressure": 0.4,
            "reframing_pressure": 0.3,
        },
        {"exploration_health": 0.4, "diversity_health": 0.5, "efficiency_health": 0.6},
        {"population_counts": {"policy": 0}, "growth_rates": {"domain": -0.3}, "extinction_risk": {"evaluation": 0.6}},
    )
    assert set(out) >= {"attention_budget", "mutation_budget", "selection_weights", "runtime_slots"}
    assert out["runtime_slots"] >= 3
