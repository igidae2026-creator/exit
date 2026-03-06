from metaos.runtime.evaluation_ecology import evaluation_ecology


def test_evaluation_ecology_reports_bounded_health_metrics() -> None:
    ecology = evaluation_ecology(
        [
            {"novelty": 0.3, "diversity": 0.35, "cost": 0.2, "fail_rate": 0.08, "pressure": {"diversity_pressure": 0.6}, "quest": {"type": "exploration"}},
            {"novelty": 0.25, "diversity": 0.32, "cost": 0.18, "fail_rate": 0.06, "pressure": {"diversity_pressure": 0.58}, "quest": {"type": "reframing"}},
        ]
    )
    assert set(ecology) == {
        "novelty_health",
        "diversity_health",
        "efficiency_health",
        "lineage_health",
        "repair_health",
        "exploration_health",
    }
    assert all(0.0 <= value <= 1.0 for value in ecology.values())
