import os
import tempfile
from pathlib import Path

from genesis.replay import replay_state
from runtime.signal_truth import append_signal, transition_signal


def test_signal_append_only_lifecycle_and_replay() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_SIGNALS"] = str(root / "signals.jsonl")
        os.environ["METAOS_EVENT_LOG"] = str(root / "events.jsonl")
        os.environ["METAOS_METRICS"] = str(root / "metrics.jsonl")
        os.environ["METAOS_REGISTRY"] = str(root / "artifact_registry.jsonl")
        os.environ["METAOS_ARCHIVE"] = str(root / "archive.jsonl")
        ingest = append_signal({"source": "human", "domain_hint": "code_domain", "payload": {"goal": "improve"}}, data_dir=str(root))
        transition_signal(str(ingest["id"]), "consumed", consumed_by="runtime:selector", data_dir=str(root))
        replayed = replay_state()
        assert replayed["signals"] >= 2
        assert replayed["signal_state"]["signals"] == 1
        assert replayed["signal_state"]["status_counts"].get("consumed", 0) == 1
