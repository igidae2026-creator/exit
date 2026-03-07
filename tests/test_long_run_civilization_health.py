import os
import tempfile
from pathlib import Path

from runtime.long_run_validation import validate_long_run


def test_long_run_civilization_health_reports_hardening_metrics() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        os.environ["METAOS_SOAK_FAST"] = "1"
        try:
            out = validate_long_run(ticks=256, seed=42, tier="smoke")
            assert "stability_score" in out
            assert "economy_balance_score" in out
            assert "guardrail_actions" in out
            assert out["replay_ok"] is True
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_SOAK_FAST", None)
