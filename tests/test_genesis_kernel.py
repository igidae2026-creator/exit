import os
import tempfile
from pathlib import Path

from artifact.registry import register_envelope
from genesis.invariants import enforce
from genesis.replay import replay_state
from genesis.spine import append_event, append_metrics


def test_genesis_kernel_truth_and_replay_are_canonical() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        try:
            append_event("tick_started", {"tick": 1})
            append_metrics({"tick": 1, "score": 0.9, "routing": {"selected_domain": "code"}})
            register_envelope(aclass="policy", atype="policy", spec={"policy": {"mutation_rate": 0.2}})
            state = replay_state()
            checks = enforce(minimum_lineages=1)
            assert state["tick"] == 1
            assert checks["append_only_logs"]["ok"] is True
            assert checks["replay_determinism"]["ok"] is True
        finally:
            os.environ.pop("METAOS_ROOT", None)
