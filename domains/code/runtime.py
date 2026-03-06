from __future__ import annotations

from typing import Any


def input() -> dict[str, Any]:
    return {"language": "python", "phase": "run"}


def generate() -> dict[str, Any]:
    return {
        "name": "code_domain",
        "constraints": {"stability": 0.6},
        "evaluation_recipe": {"score": 1.0},
        "mutation_priors": {"mutation_rate": 0.2},
    }


def evaluate(artifact: dict[str, Any]) -> dict[str, Any]:
    valid = "name" in artifact and "mutation_priors" in artifact
    return {"score": float(dict(artifact).get("score", 1.0)), "valid": valid}


def metrics(artifact: dict[str, Any]) -> dict[str, float]:
    score = float(dict(artifact).get("score", 1.0))
    return {"score": score, "novelty": 0.4, "diversity": 0.4, "cost": 0.2, "fail_rate": 0.0}


def loop() -> dict[str, Any]:
    artifact = generate()
    return {"input": input(), "artifact": artifact, "evaluation": evaluate(artifact), "metrics": metrics(artifact)}
