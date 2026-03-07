from runtime.ceiling_metrics import compute_ceiling_metrics


def test_ceiling_metrics_capture_upper_tail_and_entropy() -> None:
    history = [
        {"score": 0.62, "novelty": 0.4, "diversity": 0.5, "categories": ["alpha"], "lineages": ["l1"]},
        {"score": 0.91, "novelty": 0.8, "diversity": 0.7, "categories": ["alpha", "beta"], "lineages": ["l1", "l2"]},
    ]
    out = compute_ceiling_metrics(
        {"score": 0.92, "novelty": 0.85, "diversity": 0.72, "quality": 0.9, "categories": ["alpha", "beta"], "lineages": ["l1", "l2"]},
        history=history,
    )
    assert out["threshold_crossing_score"] > 0.0
    assert out["breakout_acceleration_score"] > 0.0
    assert out["exploration_entropy"] > 0.0
    assert out["innovation_density"] > 0.0
