import os
import tempfile
from pathlib import Path

from metaos.runtime.soak_runner import run_soak


def test_soak_runner_completes_multiple_ticks() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_REGISTRY"] = str(root / "artifact_registry.jsonl")
        os.environ["METAOS_ARCHIVE"] = str(root / "archive.jsonl")
        os.environ["METAOS_METRICS"] = str(root / "metrics.jsonl")
        os.environ["METAOS_CHECKPOINT"] = str(root / "checkpoint.json")
        os.environ["METAOS_POLICY_REGISTRY"] = str(root / "policy_registry.jsonl")
        try:
            reports = run_soak(
                [
                    {"score": 0.4, "novelty": 0.2, "diversity": 0.3, "cost": 0.2, "fail_rate": 0.1},
                    {"score": 0.5, "novelty": 0.25, "diversity": 0.35, "cost": 0.22, "fail_rate": 0.15},
                    {"score": 0.6, "novelty": 0.3, "diversity": 0.4, "cost": 0.18, "fail_rate": 0.05},
                ],
                workers=6,
            )
            assert len(reports) == 3
            assert reports[-1]["tick"] == 3
            assert Path(os.environ["METAOS_METRICS"]).exists()
            assert Path(os.environ["METAOS_POLICY_REGISTRY"]).exists()
        finally:
            os.environ.pop("METAOS_REGISTRY", None)
            os.environ.pop("METAOS_ARCHIVE", None)
            os.environ.pop("METAOS_METRICS", None)
            os.environ.pop("METAOS_CHECKPOINT", None)
            os.environ.pop("METAOS_POLICY_REGISTRY", None)
