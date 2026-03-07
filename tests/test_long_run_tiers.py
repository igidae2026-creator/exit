import os
import tempfile
from pathlib import Path

from runtime.long_run_validation import LONG_RUN_TIERS, validate_long_run


def test_long_run_tiers_are_genesis_floor() -> None:
    assert LONG_RUN_TIERS["smoke"]["ticks"] >= 256
    assert LONG_RUN_TIERS["bounded"]["ticks"] >= 4096
    assert LONG_RUN_TIERS["soak"]["ticks"] >= 50000


def test_bounded_tier_reports_floor_metrics() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        os.environ["METAOS_SOAK_FAST"] = "1"
        try:
            out = validate_long_run(ticks=4096, seed=42, tier="bounded")
            assert out["tier"] == "bounded"
            assert out["resolved_ticks"] == 4096
            assert "append_only_violation_count" in out
            assert "invariant_violation_count" in out
            assert "replay_mismatch_count" in out
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_SOAK_FAST", None)
