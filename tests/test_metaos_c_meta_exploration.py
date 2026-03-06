from metaos_c.meta_exploration import meta_exploration


def test_metaos_c_meta_exploration_mutates_discovery_rules() -> None:
    out = meta_exploration(
        {"knowledge_density": 0.6, "domain_distribution": {"default": 4}, "artifact_distribution": {"evaluation": 2, "domain": 4}},
        {"novelty_pressure": 0.7, "diversity_pressure": 0.6, "domain_shift_pressure": 0.8, "reframing_pressure": 0.3},
    )
    assert "domain_discovery_rules" in out
    assert out["domain_discovery_rules"]["spawn_threshold"] > 0.45
