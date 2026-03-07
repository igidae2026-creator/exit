from metaos.runtime.quota_allocator import allocate


def test_worker_soft_ceiling_avoids_pinning_at_max_under_normal_pressure() -> None:
    budgets = allocate(
        {
            "novelty_pressure": 0.85,
            "diversity_pressure": 0.55,
            "domain_shift_pressure": 0.2,
            "repair_pressure": 0.08,
            "efficiency_pressure": 0.12,
        },
        workers=30,
        history=[{"workers": 30}],
    )
    assert int(budgets["effective_workers"]) <= 32


def test_worker_soft_ceiling_allows_above_band_for_strong_combined_pressure() -> None:
    budgets = allocate(
        {
            "novelty_pressure": 1.0,
            "diversity_pressure": 0.8,
            "domain_shift_pressure": 0.6,
            "repair_pressure": 0.05,
            "efficiency_pressure": 0.05,
        },
        workers=30,
        history=[{"workers": 30}],
    )
    assert int(budgets["effective_workers"]) >= 29
