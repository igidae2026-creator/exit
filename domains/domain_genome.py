from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


STRATEGY_KEYS = ("quality", "novelty", "diversity", "efficiency", "cost", "usefulness", "persistence", "recombination")


@dataclass(slots=True, frozen=True)
class DomainGenome:
    adapter: str
    constraints: dict[str, Any] = field(default_factory=dict)
    evaluation_recipe: dict[str, float] = field(default_factory=dict)
    mutation_priors: dict[str, float] = field(default_factory=dict)
    seed_strategy: dict[str, float] = field(default_factory=dict)
    transfer_bias: dict[str, float] = field(default_factory=dict)

    def normalize(self, strategy: Mapping[str, Any] | None) -> dict[str, float]:
        payload = dict(self.seed_strategy)
        payload.update(dict(strategy or {}))
        normalized: dict[str, float] = {}
        for key in STRATEGY_KEYS:
            try:
                normalized[key] = max(0.0, min(1.0, float(payload.get(key, 0.0))))
            except Exception:
                normalized[key] = 0.0
        return normalized

    def mutate(self, strategy: Mapping[str, Any], *, drift: float = 0.08) -> dict[str, float]:
        base = self.normalize(strategy)
        mutated: dict[str, float] = {}
        for index, key in enumerate(STRATEGY_KEYS, start=1):
            prior = float(self.mutation_priors.get(key, self.mutation_priors.get("default", 0.1)))
            delta = ((prior * 0.6) + (drift * ((index % 3) + 1) / 3.0)) - (drift * 0.5)
            mutated[key] = max(0.0, min(1.0, base[key] + delta))
        return mutated

    def evaluate(self, strategy: Mapping[str, Any]) -> float:
        candidate = self.normalize(strategy)
        weights = self.evaluation_recipe or {"quality": 0.22, "novelty": 0.16, "diversity": 0.15, "efficiency": 0.12, "cost": -0.08, "usefulness": 0.12, "persistence": 0.08, "recombination": 0.08}
        score = 0.0
        for key, weight in weights.items():
            score += candidate.get(key, 0.0) * float(weight)
        return max(0.0, min(1.0, score))

    def transfer(self, source: Mapping[str, Any], *, pressure: float = 0.3) -> dict[str, float]:
        candidate = self.normalize(source)
        transferred = dict(candidate)
        for key, bias in self.transfer_bias.items():
            transferred[key] = max(0.0, min(1.0, transferred.get(key, 0.0) + (float(bias) * pressure)))
        return transferred

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter": self.adapter,
            "constraints": dict(self.constraints),
            "evaluation_recipe": dict(self.evaluation_recipe),
            "mutation_priors": dict(self.mutation_priors),
            "seed_strategy": dict(self.seed_strategy),
            "transfer_bias": dict(self.transfer_bias),
        }


DOMAIN_GENOMES: dict[str, DomainGenome] = {
    "code_domain": DomainGenome(
        adapter="code_domain",
        constraints={"canonical": True, "max_lineage_share": 0.68},
        evaluation_recipe={"quality": 0.22, "novelty": 0.14, "diversity": 0.12, "efficiency": 0.18, "cost": -0.08, "usefulness": 0.16, "persistence": 0.06, "recombination": 0.10},
        mutation_priors={"quality": 0.10, "novelty": 0.12, "diversity": 0.10, "efficiency": 0.14, "usefulness": 0.15, "recombination": 0.10, "default": 0.08},
        seed_strategy={"quality": 0.52, "novelty": 0.48, "diversity": 0.40, "efficiency": 0.62, "cost": 0.28, "usefulness": 0.55, "persistence": 0.44, "recombination": 0.46},
        transfer_bias={"usefulness": 0.12, "persistence": 0.08, "recombination": 0.10},
    ),
    "research": DomainGenome(
        adapter="research",
        constraints={"canonical": False},
        evaluation_recipe={"quality": 0.16, "novelty": 0.19, "diversity": 0.13, "efficiency": 0.08, "cost": -0.08, "usefulness": 0.16, "persistence": 0.10, "recombination": 0.12},
        mutation_priors={"novelty": 0.15, "diversity": 0.12, "usefulness": 0.12, "recombination": 0.12, "default": 0.08},
        seed_strategy={"quality": 0.46, "novelty": 0.58, "diversity": 0.55, "efficiency": 0.42, "cost": 0.31, "usefulness": 0.52, "persistence": 0.47, "recombination": 0.50},
        transfer_bias={"novelty": 0.12, "diversity": 0.08, "recombination": 0.12},
    ),
    "science": DomainGenome(
        adapter="science",
        constraints={"canonical": False},
        evaluation_recipe={"quality": 0.18, "novelty": 0.16, "diversity": 0.12, "efficiency": 0.09, "cost": -0.08, "usefulness": 0.14, "persistence": 0.14, "recombination": 0.11},
        mutation_priors={"quality": 0.11, "novelty": 0.13, "persistence": 0.14, "recombination": 0.11, "default": 0.08},
        seed_strategy={"quality": 0.50, "novelty": 0.53, "diversity": 0.46, "efficiency": 0.40, "cost": 0.33, "usefulness": 0.56, "persistence": 0.61, "recombination": 0.49},
        transfer_bias={"quality": 0.10, "persistence": 0.12, "usefulness": 0.08},
    ),
    "fiction": DomainGenome(
        adapter="fiction",
        constraints={"canonical": False},
        evaluation_recipe={"quality": 0.14, "novelty": 0.20, "diversity": 0.16, "efficiency": 0.05, "cost": -0.07, "usefulness": 0.10, "persistence": 0.11, "recombination": 0.17},
        mutation_priors={"novelty": 0.16, "diversity": 0.14, "recombination": 0.16, "default": 0.08},
        seed_strategy={"quality": 0.44, "novelty": 0.64, "diversity": 0.58, "efficiency": 0.35, "cost": 0.36, "usefulness": 0.42, "persistence": 0.55, "recombination": 0.63},
        transfer_bias={"novelty": 0.14, "diversity": 0.12, "recombination": 0.16},
    ),
}


def available_domain_genomes() -> dict[str, DomainGenome]:
    return dict(DOMAIN_GENOMES)


def canonical_domain_genome(name: str = "code_domain") -> DomainGenome:
    return DOMAIN_GENOMES.get(name, DOMAIN_GENOMES["code_domain"])


def domain_plugin_names() -> list[str]:
    return sorted(DOMAIN_GENOMES)
