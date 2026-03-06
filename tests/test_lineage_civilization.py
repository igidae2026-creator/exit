from runtime.lineage_ecology import assess_lineages


def test_lineage_civilization_reports_survival_and_dominance_metrics() -> None:
    out = assess_lineages(
        [
            {"lineage_id": "alpha"},
            {"lineage_id": "beta"},
            {"lineage_id": "alpha"},
            {"lineage_id": "gamma"},
        ],
        diversity_floor=2,
    )
    assert out["lineage_diversity"] > 0.0
    assert out["lineage_survival_rate"] >= 1.0
    assert out["dominance_index"] < 0.85
