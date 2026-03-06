import os
import tempfile
from pathlib import Path

from genesis.replay import replay_state
from metaos.runtime.soak_runner import run_soak


def test_multi_lineage_survival() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        os.environ["METAOS_SOAK_FAST"] = "1"
        try:
            run_soak(ticks=120, seed=42, fail_open=True)
            state = replay_state()
            assert state["lineage_state"]["surviving_lineages"] > 1
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_SOAK_FAST", None)
