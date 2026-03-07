from runtime.evaluation_evolution import evolve_evaluations


def test_evaluation_evolution_activation_exposes_active_generations() -> None:
    out = evolve_evaluations(
        {"novelty_weight": 0.2},
        {"novelty_pressure": 0.8, "diversity_pressure": 0.6, "repair_pressure": 0.1, "efficiency_pressure": 0.2},
        {"policy_stagnation": 0.7, "effective_lineage_diversity": 0.2, "domain_activation_rate": 0.2, "evaluation_dominance_index": 0.9},
    )
    assert out["evaluation_generation_count"] > 0
    assert out["active_evaluation_generations"] > 1
    assert out["evaluation_branch_rate"] > 0.0
    assert out["evaluation_diversity"] > 0.0
    assert out["active_evaluation_distribution"]
