from metaos.domains.domain_crossbreed import crossbreed


def test_domain_crossbreed_mutates_clone_when_single_domain() -> None:
    out = crossbreed({"name": "default", "constraints": {}, "evaluation_recipe": {"score": 1.0}, "mutation_priors": {"mutation_rate": 0.2}})
    assert out["name"].startswith("default")
    assert "evaluation_recipe" in out


def test_domain_crossbreed_merges_bounded_sections() -> None:
    out = crossbreed(
        {"name": "default", "constraints": {"stability": 0.5}, "evaluation_recipe": {"score": 1.0}, "mutation_priors": {"mutation_rate": 0.2}},
        {"name": "exploration_variant", "constraints": {"novelty": 0.7}, "evaluation_recipe": {"score": 0.9}, "mutation_priors": {"mutation_rate": 0.3}},
    )
    assert out["name"] == "default__exploration_variant"
    assert "stability" in out["constraints"]
    assert "novelty" in out["constraints"]
