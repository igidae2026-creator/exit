import os
import tempfile
from pathlib import Path

from kernel.spine import append_metrics
from metaos.core.supervisor import guarded_step
from metaos.kernel.replay import replay_state
from metaos.observer import pressure_engine
from metaos.runtime.oed_orchestrator import step
from validation.boundary import validate_boundary


def _genesis_env(root: Path) -> None:
    os.environ["METAOS_EVENT_LOG"] = str(root / "events.jsonl")
    os.environ["METAOS_METRICS"] = str(root / "metrics.jsonl")
    os.environ["METAOS_REGISTRY"] = str(root / "artifact_registry.jsonl")
    os.environ["METAOS_ARCHIVE"] = str(root / "archive.jsonl")
    os.environ["METAOS_CIVILIZATION_MEMORY"] = str(root / "civilization_memory.jsonl")
    os.environ["METAOS_POLICY_REGISTRY"] = str(root / "policy_registry.jsonl")
    os.environ["METAOS_EVALUATION_REGISTRY"] = str(root / "evaluation_registry.jsonl")
    os.environ["METAOS_EXPLORATION_STRATEGY_REGISTRY"] = str(root / "exploration_registry.jsonl")
    os.environ["METAOS_ALLOCATOR_REGISTRY"] = str(root / "allocator_registry.jsonl")
    os.environ["METAOS_STRATEGY_OF_STRATEGY_REGISTRY"] = str(root / "strategy_of_strategy_registry.jsonl")
    os.environ["METAOS_DOMAIN_POOL"] = str(root / "domain_pool.json")


def _clear_env() -> None:
    for key in (
        "METAOS_EVENT_LOG",
        "METAOS_METRICS",
        "METAOS_REGISTRY",
        "METAOS_ARCHIVE",
        "METAOS_CIVILIZATION_MEMORY",
        "METAOS_POLICY_REGISTRY",
        "METAOS_EVALUATION_REGISTRY",
        "METAOS_EXPLORATION_STRATEGY_REGISTRY",
        "METAOS_ALLOCATOR_REGISTRY",
        "METAOS_STRATEGY_OF_STRATEGY_REGISTRY",
        "METAOS_DOMAIN_POOL",
    ):
        os.environ.pop(key, None)


def test_genesis_boundary_validation() -> None:
    out = validate_boundary(
        {
            "human": ["constitution", "goal", "acceptance"],
            "system": ["exploration", "implementation", "validation", "evolution"],
        }
    )
    assert out["ok"] is True


def test_genesis_replay_restore_on_invalid_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _genesis_env(root)
        try:
            append_metrics({"tick": 3, "score": 0.71, "quest": {"type": "work"}})

            def _boom(_: object) -> object:
                raise RuntimeError("invalid state")

            restored = guarded_step(_boom, {"tick": 99, "workers": -1})
            assert restored["tick"] == 3
            assert restored["supervisor_mode"] == "safe_mode"
        finally:
            _clear_env()


def test_genesis_diversity_pressure_rises_on_lineage_collapse(monkeypatch) -> None:
    monkeypatch.setattr(pressure_engine, "concentration", lambda: 0.92)
    pressure = pressure_engine.pressure({"novelty": 0.4, "diversity": 0.55, "cost": 0.2, "fail_rate": 0.1})
    assert "lineage_pressure" not in pressure
    assert pressure["diversity_pressure"] > 0.6


def test_genesis_reframing_on_plateau_and_budget_exhaustion(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _genesis_env(root)
        try:
            history = [
                {"quest": {"type": "exploration"}, "routing": {"selected_domain": "default"}, "pressure": {"diversity_pressure": 0.4}}
                for _ in range(7)
            ]
            monkeypatch.setattr("metaos.runtime.oed_orchestrator.metrics_tail", lambda n=200: history)
            monkeypatch.setattr("metaos.runtime.oed_orchestrator.plateau", lambda *args, **kwargs: True)
            monkeypatch.setattr("metaos.runtime.oed_orchestrator.novelty_drop", lambda *args, **kwargs: False)
            monkeypatch.setattr("metaos.runtime.oed_orchestrator.concentration", lambda *args, **kwargs: 0.2)
            out = step(metrics={"score": 0.5, "novelty": 0.2, "diversity": 0.4, "cost": 0.2, "fail_rate": 0.1}, policy=None, workers=8)
            assert out["quest"]["type"] == "reframing"
            assert out["exploration_cycle"]["exhausted"] is True
        finally:
            _clear_env()


def test_genesis_repair_failure_escalates_to_repair_quest(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _genesis_env(root)
        try:
            history = [
                {
                    "quest": {"type": "repair"},
                    "repair": {"type": "retry_once"},
                    "routing": {"selected_domain": "default"},
                    "pressure": {"repair_pressure": 0.95, "diversity_pressure": 0.4},
                }
                for _ in range(3)
            ]
            monkeypatch.setattr("metaos.runtime.oed_orchestrator.metrics_tail", lambda n=200: history)
            monkeypatch.setattr("metaos.runtime.oed_orchestrator.plateau", lambda *args, **kwargs: False)
            monkeypatch.setattr("metaos.runtime.oed_orchestrator.novelty_drop", lambda *args, **kwargs: False)
            monkeypatch.setattr("metaos.runtime.oed_orchestrator.concentration", lambda *args, **kwargs: 0.2)
            out = step(metrics={"score": 0.3, "novelty": 0.3, "diversity": 0.5, "cost": 0.2, "fail_rate": 0.92}, policy=None, workers=8)
            assert out["quest"]["type"] == "repair"
            assert out["quest"]["escalation"] == "repair_failure"
        finally:
            _clear_env()


def test_genesis_replay_reconstructs_full_state_after_soak() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _genesis_env(root)
        os.environ["METAOS_SOAK_FAST"] = "1"
        try:
            from metaos.runtime.soak_runner import run_soak

            ticks, summary = run_soak(ticks=120, seed=42, fail_open=True)
            replayed = replay_state()
            assert ticks
            assert summary["exploration_share"] > 0.45
            assert replayed["tick"] == ticks[-1]["tick"]
            assert replayed["active_policies"]
            assert replayed["quest_state"]
            assert replayed["pressure_state"]
            assert replayed["domain_routing_state"]
            assert replayed["recovery_state"]
            assert replayed["lineage_state"]["surviving_lineages"] > 1
        finally:
            os.environ.pop("METAOS_SOAK_FAST", None)
            _clear_env()
