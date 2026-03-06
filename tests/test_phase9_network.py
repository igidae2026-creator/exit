import os
import tempfile
from pathlib import Path

from metaos.runtime.soak_runner import run_soak


def test_phase9_network_soak_creates_domains_and_keeps_meta_bounded() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_SOAK_FAST"] = "1"
        os.environ["METAOS_ROOT"] = str(root)
        os.environ["METAOS_REGISTRY"] = str(root / "artifact_registry.jsonl")
        os.environ["METAOS_ARCHIVE"] = str(root / "archive.jsonl")
        os.environ["METAOS_METRICS"] = str(root / "metrics.jsonl")
        os.environ["METAOS_CHECKPOINT"] = str(root / "checkpoint.json")
        os.environ["METAOS_POLICY_REGISTRY"] = str(root / "policy_registry.jsonl")
        os.environ["METAOS_CIVILIZATION_MEMORY"] = str(root / "civilization_memory.jsonl")
        os.environ["METAOS_EVALUATION_REGISTRY"] = str(root / "evaluation_registry.jsonl")
        os.environ["METAOS_EXPLORATION_STRATEGY_REGISTRY"] = str(root / "exploration_registry.jsonl")
        os.environ["METAOS_ALLOCATOR_REGISTRY"] = str(root / "allocator_registry.jsonl")
        os.environ["METAOS_STRATEGY_OF_STRATEGY_REGISTRY"] = str(root / "strategy_of_strategy_registry.jsonl")
        os.environ["METAOS_DOMAIN_POOL"] = str(root / "domain_pool.json")
        try:
            ticks, summary = run_soak(ticks=240, seed=21, fail_open=True)
            assert len(ticks) == 240
            assert summary["meta_share"] < 0.20
            assert summary["exploration_share"] >= 0.50
            assert summary["new_domain_count"] > 0
            assert summary["meta_exploration_count"] == 240
            assert ticks[-1]["meta_exploration"]["topology_shift"]["domain_count"] >= 2
            assert ticks[-1]["strategy_of_strategy"]
        finally:
            for key in (
                "METAOS_SOAK_FAST",
                "METAOS_ROOT",
                "METAOS_REGISTRY",
                "METAOS_ARCHIVE",
                "METAOS_METRICS",
                "METAOS_CHECKPOINT",
                "METAOS_POLICY_REGISTRY",
                "METAOS_CIVILIZATION_MEMORY",
                "METAOS_EVALUATION_REGISTRY",
                "METAOS_EXPLORATION_STRATEGY_REGISTRY",
                "METAOS_ALLOCATOR_REGISTRY",
                "METAOS_STRATEGY_OF_STRATEGY_REGISTRY",
                "METAOS_DOMAIN_POOL",
            ):
                os.environ.pop(key, None)
