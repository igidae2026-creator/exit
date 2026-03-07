from runtime.civilization_state import civilization_state


def test_policy_turnover_quality_is_derived_from_history() -> None:
    out = civilization_state(
        state={"exploration_economy_state": {"economy_balance_score": 0.7, "budget_skew": 0.1}},
        history=[
            {"policy": {"mode": "a"}, "score": 0.2},
            {"policy": {"mode": "b"}, "score": 0.4},
            {"policy": {"mode": "b"}, "score": 0.5},
            {"policy": {"mode": "c"}, "score": 0.7},
        ],
    )
    assert 0.0 <= out["policy_turnover_quality"] <= 1.0
    assert 0.0 <= out["policy_stagnation"] <= 1.0
