import os
import tempfile
from pathlib import Path

from artifact.registry import register_envelope
from genesis.replay import replay_state_hash
from genesis.spine import append_event, append_metrics


def test_replay_state_hash_is_stable_across_repeated_replays() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        try:
            append_event("tick_started", {"tick": 1})
            append_metrics({"tick": 1, "score": 0.8, "quest": {"type": "exploration"}, "routing": {"selected_domain": "alpha"}})
            register_envelope(aclass="domain", atype="domain_genome", spec={"metadata": {"lineage_id": "alpha"}, "routing": {"selected_domain": "alpha"}})
            hashes = {replay_state_hash() for _ in range(20)}
            assert len(hashes) == 1
        finally:
            os.environ.pop("METAOS_ROOT", None)
