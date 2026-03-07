from runtime.domain_lifecycle import domain_lifecycle_state


def test_domain_lineage_coverage_tracks_specialization() -> None:
    out = domain_lifecycle_state(
        {"created_domains": ["default", "science"], "active_domains": ["default", "science"], "inactive_domains": []},
        history=[
            {"domain": "default", "lineage": {"selected_lineage": "default:root"}},
            {"domain": "science", "lineage": {"selected_lineage": "science:novelty"}},
            {"domain": "science", "lineage": {"selected_lineage": "science:evaluation"}},
        ],
        pressure_state={"domain_shift_pressure": 0.6},
    )
    assert out["domain_lineage_coverage"] > 0.0
    assert len(out["lineage_domain_matrix"]["science"]) >= 2

