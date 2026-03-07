import os
import tempfile
from pathlib import Path

from runtime.long_run_validation import validate_long_run


def test_long_run_multi_lineage_reports_diversified_runtime() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        os.environ["METAOS_SOAK_FAST"] = "1"
        try:
            out = validate_long_run(profile="smoke", ticks=1024, seed=42)
            assert out["active_lineage_count"] > 1
            out = validate_long_run(ticks=4096, seed=42, tier="bounded")
            assert out["active_lineage_count"] >= 4
            assert out["dominance_index"] < 1.0
            assert out["evaluation_generations"] > 0
            assert out["diversification_intervention_count"] > 0
            assert out["forced_branch_count"] > 0 or out["branch_rate"] > 0.0
            assert out["domain_lineage_coverage"] > 0.0
            assert out["replay_ok"] is True
            assert out["threshold_checks"]["ticks"] is True
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_SOAK_FAST", None)
