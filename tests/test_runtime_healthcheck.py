import os
import subprocess
import tempfile
from pathlib import Path

from artifact.registry import register_envelope
from genesis.spine import append_event, append_metrics


def test_runtime_healthcheck_exits_zero() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        try:
            append_event("tick_started", {"tick": 1})
            append_metrics({"tick": 1, "score": 0.7, "quest": {"type": "exploration"}, "routing": {"selected_domain": "default"}})
            register_envelope(aclass="domain", atype="domain_genome", spec={"routing": {"selected_domain": "default"}})
            completed = subprocess.run(["bash", "ops/healthcheck.sh"], capture_output=True, text=True, check=False, timeout=20)
            assert completed.returncode == 0, completed.stderr
        finally:
            os.environ.pop("METAOS_ROOT", None)
