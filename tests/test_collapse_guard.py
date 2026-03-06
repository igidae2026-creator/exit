from metaos.runtime.collapse_guard import detect_guard_state


def test_collapse_guard_flags_stagnation_and_repair_storm() -> None:
    history = [
        {
            "novelty": 0.1,
            "fail_rate": 0.4,
            "repair": {"type": "retry_once"},
            "pressure": {"lineage_pressure": 0.8, "domain_shift_pressure": 0.7},
            "budgets": {"effective_workers": 6, "mutation_budget": 40, "replay_budget": 40, "repair_budget": 40, "archive_budget": 40, "domain_budget": 40},
            "routing": {"selected_domain": "default"},
        }
        for _ in range(8)
    ]
    guard = detect_guard_state(history)
    assert guard["freeze_export"] is True
    assert guard["downshift_workers"] is True
    assert guard["force_meta"] is True
    assert guard["force_reframing"] is True
