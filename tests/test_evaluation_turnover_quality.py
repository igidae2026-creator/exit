from runtime.civilization_state import civilization_state


def test_evaluation_turnover_quality_is_derived_from_history() -> None:
    out = civilization_state(
        state={"exploration_economy_state": {"economy_balance_score": 0.65, "budget_skew": 0.12}},
        history=[
            {"evaluation": {"mode": "a"}, "score": 0.2},
            {"evaluation": {"mode": "b"}, "score": 0.35},
            {"evaluation": {"mode": "b"}, "score": 0.55},
            {"evaluation": {"mode": "c"}, "score": 0.68},
        ],
    )
    assert 0.0 <= out["evaluation_turnover_quality"] <= 1.0
    assert 0.0 <= out["evaluation_stagnation"] <= 1.0
