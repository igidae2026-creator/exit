import os
import tempfile
import time
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
        os.environ["METAOS_EVENT_LOG"] = str(root / "events.jsonl")
        os.environ["METAOS_REGISTRY"] = str(root / "artifact_registry.jsonl")
        os.environ["METAOS_METRICS"] = str(root / "metrics.jsonl")
        os.environ["METAOS_ARCHIVE"] = str(root / "archive.jsonl")
        os.environ["METAOS_CHECKPOINT"] = str(root / "checkpoint.json")
        os.environ["METAOS_POLICY_REGISTRY"] = str(root / "policy_registry.jsonl")
        os.environ["METAOS_CIVILIZATION_MEMORY"] = str(root / "civilization_memory.jsonl")
        os.environ["METAOS_EVALUATION_REGISTRY"] = str(root / "evaluation_registry.jsonl")
        os.environ["METAOS_EXPLORATION_STRATEGY_REGISTRY"] = str(root / "exploration_registry.jsonl")
        os.environ["METAOS_ALLOCATOR_REGISTRY"] = str(root / "allocator_registry.jsonl")
        os.environ["METAOS_STRATEGY_OF_STRATEGY_REGISTRY"] = str(root / "strategy_of_strategy_registry.jsonl")
        os.environ["METAOS_DOMAIN_POOL"] = str(root / "domain_pool.json")
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
    "METAOS_EVENT_LOG",
    "METAOS_REGISTRY",
    "METAOS_METRICS",
    "METAOS_ARCHIVE",
    "METAOS_CHECKPOINT",
    "METAOS_POLICY_REGISTRY",
    "METAOS_CIVILIZATION_MEMORY",
    "METAOS_EVALUATION_REGISTRY",
    "METAOS_EXPLORATION_STRATEGY_REGISTRY",
    "METAOS_ALLOCATOR_REGISTRY",
    "METAOS_STRATEGY_OF_STRATEGY_REGISTRY",
    "METAOS_DOMAIN_POOL",
]


def test_phase75_distribution() -> None:
    with _soak_env():
        t0 = time.time()
        ticks, summary = run_soak(ticks=240, seed=21, fail_open=True)
        elapsed = time.time() - t0
        assert elapsed < 12.0
        assert summary["meta_share"] <= 0.30
        assert summary["exploration_share"] >= 0.45
        assert summary["reframing_count"] >= 8
        assert len([name for name, count in summary["selected_domain_counts"].items() if count > 0]) >= 2
        assert {"policy", "evaluation", "strategy_of_strategy", "domain"}.issubset(summary["selected_artifact_type_counts"])
        assert 12 <= summary["avg_workers"] <= 28
        assert "selected_domain" in ticks[-1]["routing"]
