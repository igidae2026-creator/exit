import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from metaos.runtime.soak_runner import _BufferedJsonlWriter, run_soak


@contextmanager
def _soak_env() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        old = {key: os.environ.get(key) for key in _ENV_KEYS}
        os.environ["METAOS_SOAK_FAST"] = "1"
        os.environ["METAOS_ROOT"] = str(root)
        os.environ["METAOS_REGISTRY"] = str(root / "artifact_registry.jsonl")
        os.environ["METAOS_ARCHIVE"] = str(root / "archive.jsonl")
        os.environ["METAOS_METRICS"] = str(root / "metrics.jsonl")
        os.environ["METAOS_CHECKPOINT"] = str(root / "checkpoint.json")
        os.environ["METAOS_POLICY_REGISTRY"] = str(root / "policy_registry.jsonl")
        os.environ["METAOS_CIVILIZATION_MEMORY"] = str(root / "civilization_memory.jsonl")
        os.environ["METAOS_EVALUATION_REGISTRY"] = str(root / "evaluation_registry.jsonl")
        os.environ["METAOS_EXPLORATION_STRATEGY_REGISTRY"] = str(root / "exploration_registry.jsonl")
        os.environ["METAOS_ALLOCATOR_REGISTRY"] = str(root / "allocator_registry.jsonl")
        try:
            yield root
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


_ENV_KEYS = [
    "METAOS_SOAK_FAST",
    "METAOS_ROOT",
    "METAOS_REGISTRY",
    "METAOS_ARCHIVE",
    "METAOS_METRICS",
    "METAOS_CHECKPOINT",
    "METAOS_POLICY_REGISTRY",
    "METAOS_CIVILIZATION_MEMORY",
    "METAOS_EVALUATION_REGISTRY",
    "METAOS_EXPLORATION_STRATEGY_REGISTRY",
    "METAOS_ALLOCATOR_REGISTRY",
]


def test_soak_fast_mode_keeps_api() -> None:
    with _soak_env():
        result = run_soak(ticks=12, seed=21, fail_open=True)
        ticks, summary = result
        assert len(result) == 12
        assert ticks[-1]["tick"] == 12
        assert isinstance(summary, dict)
        assert result.summary == summary


def test_soak_fast_mode_batches_persistence(monkeypatch) -> None:
    counts = {"archive": 0, "memory": 0}
    original_flush = _BufferedJsonlWriter.flush

    def counted_flush(self: _BufferedJsonlWriter) -> None:
        if self.buffer:
            if self.path.name == "archive.jsonl":
                counts["archive"] += 1
            elif self.path.name == "civilization_memory.jsonl":
                counts["memory"] += 1
        original_flush(self)

    monkeypatch.setattr(_BufferedJsonlWriter, "flush", counted_flush)
    with _soak_env():
        run_soak(ticks=25, seed=21, fail_open=True)
    assert counts["archive"] == 3
    assert counts["memory"] == 3


def test_soak_fast_mode_summary_matches_shape() -> None:
    with _soak_env():
        ticks, summary = run_soak(ticks=20, seed=11, fail_open=True)
        assert len(ticks) == 20
        assert {
            "max_workers",
            "min_workers",
            "avg_workers",
            "repair_count",
            "work_count",
            "exploration_count",
            "cross_domain_count",
            "selected_domain_counts",
            "selected_artifact_type_counts",
            "meta_count",
            "reframing_count",
            "meta_share",
            "exploration_share",
            "freeze_count",
        }.issubset(summary)
        assert isinstance(summary["avg_workers"], float)
        assert summary["max_workers"] >= summary["min_workers"]


def test_soak_fast_mode_uses_metaos_root_defaults() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        old = {key: os.environ.get(key) for key in _ENV_KEYS}
        os.environ["METAOS_SOAK_FAST"] = "1"
        os.environ["METAOS_ROOT"] = str(root)
        for key in (
            "METAOS_REGISTRY",
            "METAOS_ARCHIVE",
            "METAOS_METRICS",
            "METAOS_CIVILIZATION_MEMORY",
        ):
            os.environ.pop(key, None)
        try:
            run_soak(ticks=12, seed=21, fail_open=True)
            assert (root / "metrics.jsonl").exists()
            assert (root / "archive.jsonl").exists()
            assert (root / "archive" / "civilization_memory.jsonl").exists()
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
