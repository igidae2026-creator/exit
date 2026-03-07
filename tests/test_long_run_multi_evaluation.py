import os
import tempfile
from pathlib import Path

from runtime.long_run_validation import validate_long_run


def test_long_run_multi_evaluation_reports_plurality() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        os.environ["METAOS_SOAK_FAST"] = "1"
        try:
            out = validate_long_run(ticks=4096, seed=42, tier="bounded")
            assert out["active_evaluation_generations"] > 1
            assert out["evaluation_diversity"] > 0.0
            assert out["evaluation_dominance_index"] < 1.0
            assert len(out["active_evaluation_distribution"]) > 1
            assert out["replay_ok"] is True
            assert out["healthy"] is True
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_SOAK_FAST", None)
