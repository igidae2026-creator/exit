import os
import tempfile
from pathlib import Path

from runtime.long_run_validation import validate_long_run


def test_long_run_reports_policy_generations() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        os.environ["METAOS_SOAK_FAST"] = "1"
        try:
            out = validate_long_run(profile="smoke", ticks=1024, seed=42)
            out = validate_long_run(ticks=256, seed=42, tier="smoke")
            assert out["civilization_state"]["policy_generations"] > 0
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_SOAK_FAST", None)

