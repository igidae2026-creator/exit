import os
import tempfile
from pathlib import Path

from metaos.runtime.soak_runner import run_soak


def test_soak_summary_reports_recovery_bounds() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_REGISTRY"] = str(root / "artifact_registry.jsonl")
        os.environ["METAOS_ARCHIVE"] = str(root / "archive.jsonl")
        os.environ["METAOS_METRICS"] = str(root / "metrics.jsonl")
        os.environ["METAOS_CHECKPOINT"] = str(root / "checkpoint.json")
        os.environ["METAOS_POLICY_REGISTRY"] = str(root / "policy_registry.jsonl")
        os.environ["METAOS_CIVILIZATION_MEMORY"] = str(root / "civilization_memory.jsonl")
        os.environ["METAOS_EVALUATION_REGISTRY"] = str(root / "evaluation_registry.jsonl")
        os.environ["METAOS_EXPLORATION_STRATEGY_REGISTRY"] = str(root / "exploration_registry.jsonl")
        try:
            ticks, summary = run_soak(ticks=60, seed=11, fail_open=True)
            assert len(ticks) == 60
            assert summary["min_workers"] >= 2
            assert summary["max_workers"] >= summary["min_workers"]
            assert summary["meta_count"] < 60
        finally:
            os.environ.pop("METAOS_REGISTRY", None)
            os.environ.pop("METAOS_ARCHIVE", None)
            os.environ.pop("METAOS_METRICS", None)
            os.environ.pop("METAOS_CHECKPOINT", None)
            os.environ.pop("METAOS_POLICY_REGISTRY", None)
            os.environ.pop("METAOS_CIVILIZATION_MEMORY", None)
            os.environ.pop("METAOS_EVALUATION_REGISTRY", None)
            os.environ.pop("METAOS_EXPLORATION_STRATEGY_REGISTRY", None)
