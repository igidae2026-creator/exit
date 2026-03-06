import os
import tempfile
from pathlib import Path

from artifact.registry import register_envelope
from kernel.replay import replay_state
from kernel.spine import append_event, append_metrics


def test_kernel_replay_rebuilds_from_append_only_truth() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_EVENT_LOG"] = str(root / "events.jsonl")
        os.environ["METAOS_METRICS"] = str(root / "metrics.jsonl")
        os.environ["METAOS_REGISTRY"] = str(root / "artifact_registry.jsonl")
        try:
            append_event("tick_started", {"tick": 1})
            append_metrics({"tick": 1, "score": 0.7})
            register_envelope(aclass="policy", atype="selection_policy", spec={"policy": {"mutation_rate": 0.2}})
            state = replay_state()
            assert state["tick"] == 1
            assert state["events"] == 1
            assert state["metrics"] == 1
            assert state["artifacts"] == 1
        finally:
            for key in ("METAOS_EVENT_LOG", "METAOS_METRICS", "METAOS_REGISTRY"):
                os.environ.pop(key, None)

