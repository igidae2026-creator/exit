import os
import tempfile
from pathlib import Path

from metaos.runtime.oed_orchestrator import step


def test_budget_exhaustion_cycle_transition(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ARCHIVE"] = str(root / "archive.jsonl")
        os.environ["METAOS_CIVILIZATION_MEMORY"] = str(root / "civilization_memory.jsonl")
        os.environ["METAOS_METRICS"] = str(root / "metrics.jsonl")
        os.environ["METAOS_REGISTRY"] = str(root / "artifact_registry.jsonl")
        try:
            history = [{"quest": {"type": "exploration"}, "routing": {"selected_domain": "default"}} for _ in range(8)]
            monkeypatch.setattr("metaos.runtime.oed_orchestrator.metrics_tail", lambda n=200: history)
            monkeypatch.setattr("metaos.runtime.oed_orchestrator.plateau", lambda *args, **kwargs: False)
            monkeypatch.setattr("metaos.runtime.oed_orchestrator.novelty_drop", lambda *args, **kwargs: False)
            monkeypatch.setattr("metaos.runtime.oed_orchestrator.concentration", lambda *args, **kwargs: 0.2)
            out = step(metrics={"score": 0.4, "novelty": 0.2, "diversity": 0.3, "cost": 0.2, "fail_rate": 0.1}, policy=None, workers=6)
            assert out["exploration_cycle"]["exhausted"] is True
            assert out["quest"]["type"] == "reframing"
        finally:
            for key in ("METAOS_ARCHIVE", "METAOS_CIVILIZATION_MEMORY", "METAOS_METRICS", "METAOS_REGISTRY"):
                os.environ.pop(key, None)

