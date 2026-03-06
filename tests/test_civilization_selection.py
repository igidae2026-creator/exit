from metaos.runtime.civilization_selection import civilization_select


def test_civilization_selection_returns_selected_type_and_scores() -> None:
    out = civilization_select(
        [{"type": "policy", "base_score": 0.5}, {"type": "strategy_of_strategy", "base_score": 0.52}, {"type": "domain", "base_score": 0.48}],
        {"novelty_pressure": 0.9, "domain_shift_pressure": 0.6},
        {"mutation_bias": 0.4, "selection_bias": 0.3},
        {"exploration_health": 0.3, "repair_health": 0.8, "novelty_health": 0.4},
    )
    assert out["selected_artifact_type"] in out["selection_scores"]
    assert "strategy_of_strategy" in out["selection_scores"]
