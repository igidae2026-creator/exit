import os
import tempfile
import time
from pathlib import Path

from metaos.runtime.soak_runner import run_soak


def test_phase8_soak_summary_exposes_governor_metrics() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_SOAK_FAST"] = "1"
        os.environ["METAOS_ROOT"] = str(root)
        os.environ["METAOS_EVENT_LOG"] = str(root / "events.jsonl")
        os.environ["METAOS_REGISTRY"] = str(root / "artifact_registry.jsonl")
        os.environ["METAOS_METRICS"] = str(root / "metrics.jsonl")
        os.environ["METAOS_ARCHIVE"] = str(root / "archive.jsonl")
        os.environ["METAOS_CHECKPOINT"] = str(root / "checkpoint.json")
        os.environ["METAOS_POLICY_REGISTRY"] = str(root / "policy_registry.jsonl")
        os.environ["METAOS_CIVILIZATION_MEMORY"] = str(root / "civilization_memory.jsonl")
        os.environ["METAOS_EVALUATION_REGISTRY"] = str(root / "evaluation_registry.jsonl")
        os.environ["METAOS_EXPLORATION_STRATEGY_REGISTRY"] = str(root / "exploration_registry.jsonl")
        os.environ["METAOS_ALLOCATOR_REGISTRY"] = str(root / "allocator_registry.jsonl")
        try:
            t0 = time.time()
            ticks, summary = run_soak(ticks=96, seed=21, fail_open=True)
            elapsed = time.time() - t0
            assert elapsed < 4.0
            assert len(ticks) == 96
            assert "artifact_population_counts" in summary
            assert "domain_switch_count" in summary
            assert "strategy_of_strategy_count" in summary
            assert "governor_interventions" in summary
            assert "governance" in ticks[-1]
            assert "economy" in ticks[-1]
        finally:
            for key in (
                "METAOS_SOAK_FAST",
                "METAOS_ROOT",
                "METAOS_EVENT_LOG",
                "METAOS_REGISTRY",
                "METAOS_METRICS",
                "METAOS_ARCHIVE",
                "METAOS_CHECKPOINT",
                "METAOS_POLICY_REGISTRY",
                "METAOS_CIVILIZATION_MEMORY",
                "METAOS_EVALUATION_REGISTRY",
                "METAOS_EXPLORATION_STRATEGY_REGISTRY",
                "METAOS_ALLOCATOR_REGISTRY",
            ):
                os.environ.pop(key, None)
