import os
import tempfile
from pathlib import Path

from metaos.runtime.oed_orchestrator import step


def test_oed_phase4_returns_market_budgets_and_routing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_REGISTRY"] = str(root / "artifact_registry.jsonl")
        os.environ["METAOS_ARCHIVE"] = str(root / "archive.jsonl")
        os.environ["METAOS_METRICS"] = str(root / "metrics.jsonl")
        os.environ["METAOS_CHECKPOINT"] = str(root / "checkpoint.json")
        os.environ["METAOS_POLICY_REGISTRY"] = str(root / "policy_registry.jsonl")
        os.environ["METAOS_ALLOCATOR_REGISTRY"] = str(root / "allocator_registry.jsonl")
        os.environ["METAOS_CIVILIZATION_MEMORY"] = str(root / "civilization_memory.jsonl")
        try:
            state = step(
                metrics={"score": 0.74, "novelty": 0.24, "diversity": 0.33, "cost": 0.13, "fail_rate": 0.03},
                policy=None,
                workers=12,
                domain="default",
                parent=None,
            )
            assert "market" in state
            assert "budgets" in state
            assert "routing" in state
            assert "default" in state["routing"]["routing_weights"]
            assert state["routing"]["selected_domain"] in state["routing"]["routing_weights"]
            assert int(state["budgets"]["effective_workers"]) >= 1
        finally:
            os.environ.pop("METAOS_REGISTRY", None)
            os.environ.pop("METAOS_ARCHIVE", None)
            os.environ.pop("METAOS_METRICS", None)
            os.environ.pop("METAOS_CHECKPOINT", None)
            os.environ.pop("METAOS_POLICY_REGISTRY", None)
            os.environ.pop("METAOS_ALLOCATOR_REGISTRY", None)
            os.environ.pop("METAOS_CIVILIZATION_MEMORY", None)
