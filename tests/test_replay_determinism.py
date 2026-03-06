import os
import tempfile
from pathlib import Path

from artifact.registry import register_envelope
from kernel.replay import replay_state
from kernel.spine import append_event, append_metrics


def test_replay_determinism_on_append_only_truth() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        try:
            append_event("tick_started", {"tick": 1})
            append_metrics({"tick": 1, "score": 0.8, "quest": {"type": "exploration"}, "routing": {"selected_domain": "alpha"}})
            register_envelope(aclass="domain", atype="domain_genome", spec={"metadata": {"lineage_id": "alpha"}, "routing": {"selected_domain": "alpha"}})
            assert replay_state() == replay_state()
        finally:
            os.environ.pop("METAOS_ROOT", None)
