import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from metaos.runtime.soak_runner import run_soak


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


def test_reframing_reappears_under_sustained_novelty_collapse() -> None:
    with _soak_env():
        ticks, summary = run_soak(ticks=120, seed=21, fail_open=True)
        assert len(ticks) == 120
        assert summary["reframing_count"] >= 6
        assert any(str((tick.get("quest", {}) or {}).get("type", "")) == "reframing" for tick in ticks)
