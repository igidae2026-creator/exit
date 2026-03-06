import os
import tempfile
from pathlib import Path

from metaos.runtime.oed_orchestrator import step


def test_oed_phase5_returns_policy_stack_evaluation_meta_and_guard() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_REGISTRY"] = str(root / "artifact_registry.jsonl")
        os.environ["METAOS_ARCHIVE"] = str(root / "archive.jsonl")
        os.environ["METAOS_METRICS"] = str(root / "metrics.jsonl")
        os.environ["METAOS_CHECKPOINT"] = str(root / "checkpoint.json")
        os.environ["METAOS_POLICY_REGISTRY"] = str(root / "policy_registry.jsonl")
        os.environ["METAOS_ALLOCATOR_REGISTRY"] = str(root / "allocator_registry.jsonl")
        os.environ["METAOS_CIVILIZATION_MEMORY"] = str(root / "civilization_memory.jsonl")
        os.environ["METAOS_EVALUATION_REGISTRY"] = str(root / "evaluation_registry.jsonl")
        os.environ["METAOS_EXPLORATION_STRATEGY_REGISTRY"] = str(root / "exploration_registry.jsonl")
        try:
            state = step(
                metrics={"score": 0.69, "novelty": 0.18, "diversity": 0.27, "cost": 0.16, "fail_rate": 0.07},
                policy=None,
                workers=14,
                domain="default",
                parent=None,
            )
            assert "policy_stack" in state
            assert "evaluation" in state
            assert "guard" in state
            assert "meta_quest" in state
            assert state["routing"]["selected_domain"] == "default"
            assert Path(os.environ["METAOS_EVALUATION_REGISTRY"]).exists()
            assert Path(os.environ["METAOS_EXPLORATION_STRATEGY_REGISTRY"]).exists()
        finally:
            os.environ.pop("METAOS_REGISTRY", None)
            os.environ.pop("METAOS_ARCHIVE", None)
            os.environ.pop("METAOS_METRICS", None)
            os.environ.pop("METAOS_CHECKPOINT", None)
            os.environ.pop("METAOS_POLICY_REGISTRY", None)
            os.environ.pop("METAOS_ALLOCATOR_REGISTRY", None)
            os.environ.pop("METAOS_CIVILIZATION_MEMORY", None)
            os.environ.pop("METAOS_EVALUATION_REGISTRY", None)
            os.environ.pop("METAOS_EXPLORATION_STRATEGY_REGISTRY", None)
