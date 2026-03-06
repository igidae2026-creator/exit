import os
import tempfile
from pathlib import Path

from artifact.registry import register_envelope
from kernel.replay import replay_state
from kernel.spine import append_event, append_metrics


def _clear_replay_env() -> None:
    for key in ("METAOS_ROOT", "METAOS_EVENT_LOG", "METAOS_METRICS", "METAOS_REGISTRY", "METAOS_ARCHIVE"):
        os.environ.pop(key, None)


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
            _clear_replay_env()


def test_kernel_replay_uses_metaos_root_when_set() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        try:
            (root / "events.jsonl").write_text('{"event_type":"tick_started","payload":{"tick":7}}\n', encoding="utf-8")
            (root / "metrics.jsonl").write_text('{"tick":7,"score":0.9,"routing":{"selected_domain":"alpha"}}\n', encoding="utf-8")
            (root / "artifact_registry.jsonl").write_text(
                '{"artifact_id":"a1","artifact_type":"policy","payload":{"metadata":{"lineage_id":"alpha"},"routing":{"selected_domain":"alpha"}}}\n',
                encoding="utf-8",
            )
            (root / "archive.jsonl").write_text('{"kind":"policy","payload":{"mutation_rate":0.2}}\n', encoding="utf-8")
            state = replay_state()
            assert state["tick"] == 7
            assert state["events"] == 1
            assert state["metrics"] == 1
            assert state["artifacts"] == 1
            assert state["active_policies"] == {"mutation_rate": 0.2}
        finally:
            _clear_replay_env()


def test_kernel_replay_ignores_stale_repo_runtime_when_metaos_root_set() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        stale = Path(".metaos_runtime/data")
        stale.mkdir(parents=True, exist_ok=True)
        stale_metrics = stale / "metrics.jsonl"
        original = stale_metrics.read_text(encoding="utf-8") if stale_metrics.exists() else None
        stale_metrics.write_text('{"tick":999}\n', encoding="utf-8")
        os.environ["METAOS_ROOT"] = str(root)
        try:
            (root / "metrics.jsonl").write_text('{"tick":3,"score":0.4}\n', encoding="utf-8")
            state = replay_state()
            assert state["tick"] == 3
            assert state["metrics"] == 1
        finally:
            if original is None:
                stale_metrics.unlink(missing_ok=True)
            else:
                stale_metrics.write_text(original, encoding="utf-8")
            _clear_replay_env()


def test_kernel_replay_is_deterministic() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        try:
            (root / "events.jsonl").write_text('{"event_type":"tick_started","payload":{"tick":5}}\n', encoding="utf-8")
            (root / "metrics.jsonl").write_text(
                '{"tick":5,"score":0.5,"quest":{"type":"exploration"},"pressure":{"novelty_pressure":0.3},"routing":{"selected_domain":"beta"}}\n',
                encoding="utf-8",
            )
            (root / "artifact_registry.jsonl").write_text(
                '{"artifact_id":"a1","artifact_type":"artifact","parent_ids":[],"payload":{"metadata":{"lineage_id":"beta"},"routing":{"selected_domain":"beta"}}}\n',
                encoding="utf-8",
            )
            (root / "archive.jsonl").write_text('{"kind":"quest","payload":{"type":"exploration"}}\n', encoding="utf-8")
            first = replay_state()
            second = replay_state()
            assert first == second
        finally:
            _clear_replay_env()
