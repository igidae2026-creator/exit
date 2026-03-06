import os
import tempfile
from pathlib import Path

from metaos.runtime.oed_orchestrator import step


def test_phase8_governance_outputs_population_governance_and_economy() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_REGISTRY"] = str(root / "artifact_registry.jsonl")
        os.environ["METAOS_METRICS"] = str(root / "metrics.jsonl")
        os.environ["METAOS_ARCHIVE"] = str(root / "archive.jsonl")
        os.environ["METAOS_CIVILIZATION_MEMORY"] = str(root / "civilization_memory.jsonl")
        os.environ["METAOS_POLICY_REGISTRY"] = str(root / "policy_registry.jsonl")
        os.environ["METAOS_EVALUATION_REGISTRY"] = str(root / "evaluation_registry.jsonl")
        os.environ["METAOS_EXPLORATION_STRATEGY_REGISTRY"] = str(root / "exploration_registry.jsonl")
        os.environ["METAOS_ALLOCATOR_REGISTRY"] = str(root / "allocator_registry.jsonl")
        os.environ["METAOS_STRATEGY_OF_STRATEGY_REGISTRY"] = str(root / "strategy_of_strategy_registry.jsonl")
        os.environ["METAOS_DOMAIN_POOL"] = str(root / "domain_pool.json")
        try:
            out = step(
                metrics={"score": 0.58, "novelty": 0.2, "diversity": 0.22, "cost": 0.21, "fail_rate": 0.05},
                policy=None,
                workers=12,
            )
            assert "population" in out
            assert "governance" in out
            assert "economy" in out
            assert "policy_budget" in out["budgets"]
            assert "evaluation_budget" in out["budgets"]
        finally:
            for key in (
                "METAOS_REGISTRY",
                "METAOS_METRICS",
                "METAOS_ARCHIVE",
                "METAOS_CIVILIZATION_MEMORY",
                "METAOS_POLICY_REGISTRY",
                "METAOS_EVALUATION_REGISTRY",
                "METAOS_EXPLORATION_STRATEGY_REGISTRY",
                "METAOS_ALLOCATOR_REGISTRY",
                "METAOS_STRATEGY_OF_STRATEGY_REGISTRY",
                "METAOS_DOMAIN_POOL",
            ):
                os.environ.pop(key, None)

