from runtime.self_tuning_guardrails import self_tuning_guardrails


def test_self_tuning_guardrails_remain_bounded() -> None:
    out = self_tuning_guardrails(
        {"dominance_index": 0.8},
        {"economy_balance_score": 0.35},
        {"stability_score": 0.3, "drift_score": 0.6, "stagnation_score": 0.7, "overexpansion_score": 0.4, "underexploration_score": 0.5},
    )
    assert out["guardrail_state"]["bounded"] is True
    assert all(0.0 <= value <= 1.0 for value in out["tuned_thresholds"].values())
    assert isinstance(out["guardrail_actions"], list)
