from runtime.lineage_branching import lineage_branching


def test_lineage_branching_creates_multiple_active_lineages() -> None:
    out = lineage_branching(
        [{"routing": {"selected_lineage": "default:root"}} for _ in range(10)],
        {"novelty_pressure": 0.8, "domain_shift_pressure": 0.7},
        domain="default",
        tick=12,
        evaluation_generations=3,
        policy_stagnation=0.7,
    )
    assert out["active_lineage_count"] > 1
    assert out["branch_rate"] > 0.0

