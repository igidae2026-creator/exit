import os
import tempfile
from pathlib import Path

from artifact.registry import register_envelope
from kernel.replay import replay_state
from kernel.spine import append_event, append_metrics
from runtime.replay_state import replay_ops_state


def test_replay_determinism_on_append_only_truth() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        try:
            append_event("tick_started", {"tick": 1})
            append_metrics({"tick": 1, "score": 0.8, "quest": {"type": "exploration"}, "routing": {"selected_domain": "alpha"}})
            register_envelope(aclass="domain", atype="domain_genome", spec={"metadata": {"lineage_id": "alpha"}, "routing": {"selected_domain": "alpha"}})
            assert replay_state() == replay_state()
            assert replay_ops_state()["automatic_replay_restore_ready"] is True
        finally:
            os.environ.pop("METAOS_ROOT", None)


def test_replay_ops_uses_canonical_repo_runtime_defaults() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        previous_cwd = Path.cwd()
        os.chdir(root)
        try:
            data_dir = root / ".metaos_runtime" / "data"
            state_dir = root / ".metaos_runtime" / "state"
            data_dir.mkdir(parents=True, exist_ok=True)
            state_dir.mkdir(parents=True, exist_ok=True)
            (data_dir / "events.jsonl").write_text('{"event_type":"tick_started","payload":{"tick":2}}\n', encoding="utf-8")
            (data_dir / "metrics.jsonl").write_text('{"tick":2,"score":0.4}\n', encoding="utf-8")
            (data_dir / "artifact_registry.jsonl").write_text(
                '{"artifact_id":"a1","artifact_type":"policy","payload":{"metadata":{"lineage_id":"alpha"},"routing":{"selected_domain":"alpha"}}}\n',
                encoding="utf-8",
            )
            (state_dir / "checkpoint.json").write_text('{"tick":2,"best_score":0.4}\n', encoding="utf-8")
            replay_ops = replay_ops_state()
            assert replay_ops["truth_row_count"] == 3
            assert replay_ops["automatic_replay_restore_ready"] is True
        finally:
            os.chdir(previous_cwd)
