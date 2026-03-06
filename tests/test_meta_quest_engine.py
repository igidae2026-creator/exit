from metaos.runtime.meta_quest_engine import meta_quest


def test_meta_quest_requires_novelty_plus_structural_trigger() -> None:
    quest = meta_quest(
        {"novelty_pressure": 0.95, "repair_pressure": 0.4, "diversity_pressure": 0.9, "domain_shift_pressure": 0.2},
        recent_state={"plateau_streak": 3, "repair_cycle_streak": 3, "novelty_low_streak": 3, "lineage_high_streak": 3},
    )
    assert quest is not None
    assert quest["type"] == "meta"
    assert "novelty_sustained_low" in quest["reasons"]
    assert "diversity_collapse_sustained" in quest["reasons"]


def test_meta_quest_returns_none_for_novelty_only() -> None:
    assert meta_quest({"novelty_pressure": 0.95, "repair_pressure": 0.1}, recent_state={"novelty_low_streak": 3}) is None
