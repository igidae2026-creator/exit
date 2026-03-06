from __future__ import annotations


def seed_genome() -> dict[str, object]:
    return {
        "name": "code_domain",
        "constraints": {"stability": 0.6},
        "evaluation_recipe": {"score": 1.0},
        "mutation_priors": {"mutation_rate": 0.2},
    }

