from metaos.runtime.exploration_market_stability import stabilize_market


def test_market_stability_prevents_runaway_bias() -> None:
    out = stabilize_market(
        {"mutation_bias": 0.9, "selection_bias": 0.1, "archive_bias": 0.1, "repair_bias": 0.8, "domain_budget_bias": 0.1},
        previous={"mutation_bias": 0.2, "selection_bias": 0.2, "archive_bias": 0.2, "repair_bias": 0.2, "domain_budget_bias": 0.2},
        guard={"reset_mutation_bias": True, "repair_storm": True},
    )
    assert out["mutation_bias"] <= 0.24
    assert out["repair_bias"] >= 0.22
    assert round(sum(out.values()), 6) == 1.0
