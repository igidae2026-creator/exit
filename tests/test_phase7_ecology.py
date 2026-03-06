import os
import tempfile
from pathlib import Path

from metaos.runtime.oed_orchestrator import step


def test_phase7_ecology_surfaces_new_fields() -> None:
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
                metrics={"score": 0.61, "novelty": 0.22, "diversity": 0.24, "cost": 0.19, "fail_rate": 0.06},
                policy=None,
                workers=12,
                domain="default",
            )
            assert "ecology" in out
            assert "strategy_of_strategy" in out
            assert "strategy_of_strategy_artifact_id" in out
            assert "civilization_selection" in out
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

