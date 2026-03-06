from metaos.runtime.lineage_ecology import assess_lineages


def test_lineage_ecology_preserves_diversity_floor() -> None:
    out = assess_lineages(
        [
            {"lineage_id": "alpha"},
            {"lineage_id": "beta"},
            {"lineage_id": "alpha"},
        ],
        diversity_floor=2,
    )
    assert out["surviving_lineages"] == 2
    assert out["diversity_floor_ok"] is True
    assert out["single_lineage_dominance"] is False
