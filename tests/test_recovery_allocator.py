from metaos.runtime.recovery_allocator import recover_budgets


def test_recovery_allocator_recovers_from_worker_floor() -> None:
    budgets = recover_budgets(
        {"worker_budget": 2, "workers": 2, "effective_workers": 2, "mutation_budget": 4, "repair_budget": 70, "replay_budget": 3, "archive_budget": 2, "domain_budget": 2},
        {"repair_storm": False, "downshift_workers": False},
        history=[{"workers": 4}],
    )
    assert int(budgets["effective_workers"]) >= 3
    assert 8.0 <= float(budgets["mutation_budget"]) <= 80.0
    assert 0.0 <= float(budgets["repair_budget"]) <= 60.0
