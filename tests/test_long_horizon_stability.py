from runtime.long_horizon_stability import long_horizon_stability


def test_long_horizon_stability_reports_meaningful_scores() -> None:
    out = long_horizon_stability(
        {
            "knowledge_density": 0.6,
            "memory_growth": 0.4,
            "dominance_index": 0.35,
            "lineage_survival_rate": 0.8,
            "created_domain_count": 4,
            "active_domain_count": 3,
            "domain_activation_rate": 0.75,
            "policy_stagnation": 0.2,
            "evaluation_stagnation": 0.25,
        },
        {"economy_balance_score": 0.7, "budget_skew": 0.18},
        {"dominance_index": 0.35},
        history=[{"policy": {"id": 1}, "evaluation": {"id": 1}, "score": 0.7} for _ in range(10)],
    )
    assert 0.0 <= out["stability_score"] <= 1.0
    assert 0.0 <= out["drift_score"] <= 1.0
    assert isinstance(out["stability_actions"], list)
