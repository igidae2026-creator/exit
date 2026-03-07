from runtime.lineage_ecology import assess_lineages


def test_lineage_health_tracks_dormancy_and_fake_diversity() -> None:
    out = assess_lineages(
        [
            {"lineage_id": "alpha", "count": 8},
            {"lineage_id": "beta", "count": 1},
            {"lineage_id": "gamma", "count": 1},
        ],
        diversity_floor=3,
    )
    assert out["dormant_lineage_count"] >= 1
    assert "effective_lineage_diversity" in out
    assert isinstance(out["lineage_actions"], list)
