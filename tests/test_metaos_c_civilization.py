from metaos_c import CivilizationState, evolve_civilization


def test_metaos_c_civilization_accumulates_memory_and_domains() -> None:
    state = CivilizationState()
    out = evolve_civilization({"selected_experiments": ["code", "research"], "strategy_scores": {"code": 0.9}}, state)
    assert "research" in out["civilization_state"].domains
    assert out["memory"]["archive_summaries"]
    assert out["topology"]["domain_count"] >= 2
