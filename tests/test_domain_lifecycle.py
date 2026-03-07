from runtime.domain_lifecycle import domain_lifecycle_state


def test_domain_lifecycle_reports_retired_and_resurrectable_sets() -> None:
    out = domain_lifecycle_state(
        {"created_domains": ["default", "alpha", "beta"], "active_domains": ["default"], "inactive_domains": ["alpha", "beta"]},
        history=[{"domain": "default"} for _ in range(8)] + [{"domain": "alpha"}],
        pressure_state={"domain_shift_pressure": 0.8, "diversity_pressure": 0.7, "novelty_pressure": 0.6},
    )
    assert "retired_domains" in out
    assert "resurrectable_domains" in out
    assert out["resurrectable_domain_count"] >= 0
