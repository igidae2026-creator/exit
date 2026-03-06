import os
import tempfile
import time
from pathlib import Path

from metaos.runtime.soak_runner import run_soak


def test_phase7_soak_summary_includes_civilization_ecology_metrics() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_SOAK_FAST"] = "1"
        os.environ["METAOS_ROOT"] = str(root)
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
            t0 = time.time()
            ticks, summary = run_soak(ticks=48, seed=21, fail_open=True)
            elapsed = time.time() - t0
            assert elapsed < 3.0
            assert len(ticks) == 48
            assert "selected_domain_counts" in summary
            assert "selected_artifact_type_counts" in summary
            assert "meta_share" in summary
            assert "exploration_share" in summary
            assert "ecology" in ticks[-1]
            assert "civilization_selection" in ticks[-1]
        finally:
            for key in (
                "METAOS_SOAK_FAST",
                "METAOS_ROOT",
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
