from metaos.runtime.meta_cooldown import quest_cooldown
from metaos.runtime.meta_quest_engine import meta_quest


def test_meta_cooldown_locks_repeated_meta() -> None:
    state = quest_cooldown({"meta_repeat": 2, "reframing_repeat": 0, "repair_repeat": 0, "guard_active": 1})
    assert state["meta_locked"] is True
    assert state["preferred_type"] == "exploration"


def test_meta_quest_respects_cooldown() -> None:
    quest = meta_quest({"novelty_pressure": 0.95, "repair_pressure": 0.1}, recent_state={"novelty_low_streak": 3, "meta_repeat": 2})
    assert quest is None
