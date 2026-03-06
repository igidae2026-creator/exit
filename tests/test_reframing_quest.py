from metaos.runtime.quest_system import should_reframe, spawn_quest


def test_reframing_quest_when_plateau_detected() -> None:
    pressure = {
        "repair_pressure": 0.2,
        "reframing_pressure": 0.1,
        "domain_shift_pressure": 0.1,
        "diversity_pressure": 0.2,
        "novelty_pressure": 0.2,
    }
    assert should_reframe(pressure, plateau_hit=True)
    quest = spawn_quest(pressure, plateau_hit=True)
    assert quest["type"] == "reframing"


def test_reframing_quest_when_lineage_high() -> None:
    pressure = {
        "repair_pressure": 0.2,
        "reframing_pressure": 0.0,
        "domain_shift_pressure": 0.0,
        "diversity_pressure": 0.2,
        "novelty_pressure": 0.2,
    }
    quest = spawn_quest(pressure, lineage_high=True, novelty_low_sustained=False)
    assert quest["type"] == "reframing"
