import os
import tempfile
from pathlib import Path

from runtime.long_run_validation import run_long_run_validation


def test_long_run_validation_reports_healthy_runtime() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        os.environ["METAOS_SOAK_FAST"] = "1"
        try:
            out = run_long_run_validation(profile="smoke", ticks=1024, seed=42, fail_open=False)
            assert out["replay_ok"] is True
            assert out["memory_growth"] > 0.0
            assert "threshold_checks" in out
            assert out["threshold_checks"]["ticks"] is True
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_SOAK_FAST", None)
