from ecosystem.artifact_market import artifact_market_state


def test_artifact_market_tracks_supply_demand_and_adoption() -> None:
    out = artifact_market_state(
        [
            {"artifacts": ["a1", "a2"], "wanted_artifacts": ["a2", "a3"]},
            {"artifacts": ["a2"], "wanted_artifacts": ["a1"]},
        ]
    )["artifact_market"]
    assert out["artifact_supply"]["a2"] == 2
    assert out["artifact_demand"]["a1"] == 1
    assert 0.0 <= out["artifact_adoption_rate"]["a2"] <= 1.0
