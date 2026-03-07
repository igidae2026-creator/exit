import os
import tempfile
from pathlib import Path

from runtime.long_run_validation import validate_long_run


def test_long_run_reports_created_domains_in_distribution() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        os.environ["METAOS_SOAK_FAST"] = "1"
        try:
            out = validate_long_run(ticks=240, seed=21)
            assert out["summary"]["new_domain_count"] > 0
            distribution = out["civilization_state"]["domain_distribution"]
            assert any(name != "default" and value > 0.0 for name, value in distribution.items())
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_SOAK_FAST", None)
