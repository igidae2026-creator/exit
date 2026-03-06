from metaos.runtime.meta_exploration import meta_exploration


def test_meta_exploration_mutates_strategy_and_requests_domain_growth() -> None:
    history = [
        {
            "domain": "default",
            "routing": {"selected_domain": "default"},
            "pressure": {"novelty_pressure": 0.82, "domain_shift_pressure": 0.74},
            "strategy_of_strategy": {
                "exploration_emphasis": 0.34,
                "diversification_emphasis": 0.18,
                "reframing_emphasis": 0.11,
                "recombination_emphasis": 0.19,
                "stabilization_emphasis": 0.18,
            },
        }
        for _ in range(12)
    ]
    ecology = {"exploration_health": 0.32, "diversity_health": 0.28, "novelty_health": 0.36}
    population = {"population_counts": {"evaluation": 1, "domain": 4}}

    out = meta_exploration(history, ecology, population)

    assert set(out) == {"strategy_mutation", "evaluation_mutation", "domain_creation", "topology_shift"}
    assert out["strategy_mutation"]["exploration_emphasis"] > 0.0
    assert out["evaluation_mutation"]["diversity"] > 0.0
    assert out["domain_creation"] is not None
    assert out["topology_shift"]["mode"] == "expand"
