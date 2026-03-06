from strategy.quest_portfolio import quest_slots


def test_quest_runtime_has_fixed_three_slots() -> None:
    slots = quest_slots({"novelty_pressure": 0.8, "diversity_pressure": 0.7, "repair_pressure": 0.1, "domain_shift_pressure": 0.0, "reframing_pressure": 0.0})
    assert isinstance(dict(slots.continuity_slot), dict)
    assert isinstance(dict(slots.frontier_slot), dict)
    assert isinstance(dict(slots.escape_slot), dict)

