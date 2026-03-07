from runtime.evaluation_lifecycle import evaluation_lifecycle


def test_evaluation_lifecycle_tracks_active_dormant_and_distribution() -> None:
    history = [
        {"evaluation": {"regime": "novelty"}},
        {"evaluation": {"regime": "diversity"}},
        {"evaluation": {"regime": "coverage"}},
        {"evaluation": {"regime": "novelty"}},
        {"evaluation": {"regime": "diversity"}},
    ]
    out = evaluation_lifecycle(history)
    assert out["evaluation_generations"] >= 3
    assert out["active_evaluation_generations"] > 1
    assert out["evaluation_diversity"] > 0.0
    assert out["evaluation_dominance_index"] < 1.0
    assert out["active_evaluation_distribution"]
