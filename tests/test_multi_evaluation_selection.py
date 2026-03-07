from runtime.orchestration.selection_stage import pluralized_selection


def test_pluralized_selection_breaks_single_evaluation_monopoly() -> None:
    out = pluralized_selection(
        {
            "selected_artifact_type": "evaluation",
            "selection_scores": {"evaluation": 0.9, "domain": 0.7},
        },
        {
            "active_evaluation_generations": 1,
            "evaluation_dominance_index": 0.92,
        },
        tick=5,
    )
    assert out["selected_artifact_type"] != "evaluation"
    assert "selection_scores" in out
