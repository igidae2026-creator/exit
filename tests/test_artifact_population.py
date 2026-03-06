from metaos.runtime.artifact_population import artifact_population


def test_artifact_population_reports_counts_growth_and_extinction() -> None:
    history = [
        {"civilization_selection": {"selected_artifact_type": "policy"}},
        {"civilization_selection": {"selected_artifact_type": "policy"}},
        {"civilization_selection": {"selected_artifact_type": "domain"}},
        {"civilization_selection": {"selected_artifact_type": "strategy_of_strategy"}},
    ]
    out = artifact_population(history)
    assert set(out) == {"population_counts", "growth_rates", "extinction_risk"}
    assert out["population_counts"]["policy"] >= 1
    assert "domain" in out["growth_rates"]
    assert "repair" in out["extinction_risk"]

