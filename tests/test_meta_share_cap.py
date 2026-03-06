from metaos.runtime.meta_cooldown import quest_cooldown
from metaos.runtime.meta_quest_engine import meta_quest


def test_meta_share_cap_locks_meta_and_prefers_work_or_exploration() -> None:
    cooldown_state = quest_cooldown(
        {"meta_repeat": 0, "reframing_repeat": 0, "repair_repeat": 0, "guard_active": 0, "meta_share": 0.5}
    )
    assert cooldown_state["meta_locked"] is True
    assert cooldown_state["preferred_type"] in {"work", "exploration"}


def test_meta_share_cap_forces_exploration_when_extreme() -> None:
    cooldown_state = quest_cooldown(
        {"meta_repeat": 0, "reframing_repeat": 0, "repair_repeat": 0, "guard_active": 0, "meta_share": 0.61}
    )
    assert cooldown_state["meta_locked"] is True
    assert cooldown_state["preferred_type"] == "exploration"
    assert cooldown_state["force_exploration"] is True


def test_meta_share_cap_blocks_meta_quest() -> None:
    quest = meta_quest(
        {"novelty_pressure": 0.96, "diversity_pressure": 0.9, "repair_pressure": 0.1},
        recent_state={"novelty_low_streak": 3, "lineage_high_streak": 3, "meta_share": 0.55},
    )
    assert quest is None
