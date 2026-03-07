from runtime.long_horizon_stability import long_horizon_stability
from runtime.self_tuning_guardrails import self_tuning_guardrails


def test_guardrail_diversification_triggers_on_concentration_streak() -> None:
    stability = long_horizon_stability(
        {
            "knowledge_density": 0.8,
            "memory_growth": 0.6,
            "dominance_index": 0.95,
            "lineage_survival_rate": 0.3,
            "created_domain_count": 3,
            "active_domain_count": 1,
            "domain_activation_rate": 0.2,
            "policy_stagnation": 0.8,
            "evaluation_stagnation": 0.7,
            "concentration_streak": 9,
        },
        {"economy_balance_score": 0.5, "budget_skew": 0.3},
        {"dominance_index": 0.95},
        history=[{"policy": {"id": i}} for i in range(20)],
    )
    guardrails = self_tuning_guardrails({"dominance_index": 0.95}, {"economy_balance_score": 0.5}, stability)
    assert "force_branching_pressure" in stability["stability_actions"]
    assert "force_branching_pressure" in guardrails["guardrail_actions"]

