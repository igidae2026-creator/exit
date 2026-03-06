from metaos.runtime.domain_creation import domain_creation


def test_domain_creation_returns_new_domain_genome_when_pressure_is_high() -> None:
    out = domain_creation(
        {
            "exploration_emphasis": 0.36,
            "diversification_emphasis": 0.22,
            "recombination_emphasis": 0.2,
            "stabilization_emphasis": 0.14,
        },
        {
            "exploration_health": 0.34,
            "diversity_health": 0.29,
            "domain_count": 3,
            "knowledge_flow": 0.12,
        },
        {"novelty_pressure": 0.78, "domain_shift_pressure": 0.71},
    )

    assert out is not None
    assert out["name"].startswith("meta_domain_")
    assert out["constraints"]["novelty"] >= 0.45
    assert "mutation_rate" in out["mutation_priors"]


def test_domain_creation_skips_when_ecology_is_healthy() -> None:
    out = domain_creation(
        {
            "exploration_emphasis": 0.2,
            "diversification_emphasis": 0.12,
            "recombination_emphasis": 0.08,
        },
        {"exploration_health": 0.82, "diversity_health": 0.79, "domain_count": 4, "knowledge_flow": 0.42},
        {"novelty_pressure": 0.18, "domain_shift_pressure": 0.12},
    )
    assert out is None
