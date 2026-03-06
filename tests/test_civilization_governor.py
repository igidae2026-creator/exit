from metaos.runtime.civilization_governor import civilization_governor


def test_civilization_governor_detects_drift_and_intervention() -> None:
    history = [{"civilization_selection": {"selected_artifact_type": "domain"}} for _ in range(12)]
    out = civilization_governor(
        history,
        {"novelty_health": 0.4, "diversity_health": 0.2, "efficiency_health": 0.6, "repair_health": 0.9},
        {"selection_bias": 0.3},
    )
    assert set(out) >= {"population_pressure", "artifact_overproduction", "ecosystem_balance", "selection_drift"}
    assert out["intervention"] is True

