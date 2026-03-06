from metaos.runtime.pressure_model import CANONICAL_PRESSURES, compute_pressure


def test_pressure_model_exposes_canonical_pressures_and_budgets() -> None:
    out = compute_pressure(
        {"score": 0.4, "novelty": 0.2, "diversity": 0.3, "cost": 0.4, "fail_rate": 0.2},
        ecology={"exploration_health": 0.3, "diversity_health": 0.4},
        population={"population_counts": {"policy": 0}, "growth_rates": {"domain": -0.2}, "extinction_risk": {"evaluation": 0.7}},
    )
    assert set(CANONICAL_PRESSURES).issubset(out["pressure"])
    assert "mutation_budget" in out["resource_allocation"]
    assert "selection_weights" in out["resource_allocation"]
    assert out["mutation_bias"] >= 0.0
    assert out["selection_bias"] >= 0.0
