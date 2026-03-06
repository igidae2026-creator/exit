from metaos.domains.domain_recombination import recombine


def test_domain_recombination_merges_two_genomes_safely() -> None:
    merged = recombine(
        {
            "name": "default",
            "constraints": {"risk": 0.2},
            "evaluation_recipe": {"score": 0.8},
            "mutation_priors": {"mutation_rate": 0.2},
        },
        {
            "name": "default",
            "constraints": {"risk": 0.6},
            "evaluation_recipe": {"score": 0.4},
            "mutation_priors": {"mutation_rate": 0.5},
        },
        {"domain_shift_pressure": 0.8, "reframing_pressure": 0.6},
    )
    assert merged["name"] == "default"
    assert 0.0 <= merged["constraints"]["risk"] <= 1.0
    assert 0.0 <= merged["mutation_priors"]["mutation_rate"] <= 1.0


def test_domain_recombination_supports_single_domain_mode() -> None:
    clone = recombine({"name": "default", "mutation_priors": {"mutation_rate": 0.2}}, None, {"domain_shift_pressure": 0.5})
    assert clone["name"] == "default"
    assert 0.0 <= clone["mutation_priors"]["mutation_rate"] <= 1.0
