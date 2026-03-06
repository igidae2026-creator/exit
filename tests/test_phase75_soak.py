import os
import tempfile
from pathlib import Path

from metaos.runtime.soak_runner import run_soak


def test_phase75_soak_last_tick_exposes_new_fields() -> None:
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
        os.environ["METAOS_STRATEGY_OF_STRATEGY_REGISTRY"] = str(root / "strategy_of_strategy_registry.jsonl")
        os.environ["METAOS_DOMAIN_POOL"] = str(root / "domain_pool.json")
        try:
            ticks, summary = run_soak(ticks=24, seed=21, fail_open=True)
            last = ticks[-1]
            assert "ecology" in last
            assert "strategy_of_strategy" in last
            assert "civilization_selection" in last
            assert "selected_domain_counts" in summary
            assert "selected_artifact_type_counts" in summary
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
                "METAOS_STRATEGY_OF_STRATEGY_REGISTRY",
                "METAOS_DOMAIN_POOL",
            ):
                os.environ.pop(key, None)
