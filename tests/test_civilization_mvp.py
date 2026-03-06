from __future__ import annotations

import json
from pathlib import Path

from core.artifact import create_artifact
from core.event_log import append_event, append_jsonl, ensure_spine
from core.quest import ensure_quest
from core.kernel_adapter import KernelAdapter
from core.replay import replay_state
from core.supervisor import Supervisor
from evolution.pressure_engine import compute_pressures
from evolution.quest_generator import generate_quest


def test_append_only_invariant(tmp_path: Path) -> None:
    ensure_spine(tmp_path / "data")
    events_path = tmp_path / "data" / "events.jsonl"
    before = events_path.stat().st_size
    append_event("alpha", {"tick": 1}, data_dir=tmp_path / "data")
    middle = events_path.stat().st_size
    append_event("beta", {"tick": 2}, data_dir=tmp_path / "data")
    after = events_path.stat().st_size
    assert before <= middle < after


def test_replay_reconstructs_state(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    artifact_dir = tmp_path / "artifact_store"
    ensure_spine(data_dir)
    create_artifact(
        "policy",
        {"selection_bias": "novelty"},
        tick=1,
        artifact_dir=artifact_dir,
        data_dir=str(data_dir),
    )
    append_event("cycle_completed", {"tick": 1, "best_score": 0.7, "supervisor_mode": "normal"}, data_dir=data_dir)
    state = replay_state(str(data_dir))
    assert state.tick == 1
    assert state.best_score == 0.7
    assert state.artifacts_by_kind["policy"] == 1


def test_lineage_survives(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    artifact_dir = tmp_path / "artifact_store"
    parent = create_artifact("strategy", {"value": 1}, tick=1, artifact_dir=artifact_dir, data_dir=str(data_dir))
    child = create_artifact(
        "output",
        {"value": 2},
        parent_ids=[parent.artifact_id],
        tick=2,
        artifact_dir=artifact_dir,
        data_dir=str(data_dir),
    )
    state = replay_state(str(data_dir))
    assert state.artifacts[child.artifact_id]["parent_ids"] == [parent.artifact_id]


def test_plateau_causes_reexploration_or_meta_quest(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    ensure_spine(data_dir)
    for tick in range(1, 5):
        append_event("cycle_completed", {"tick": tick, "best_score": 0.5, "supervisor_mode": "normal"}, data_dir=data_dir)
        append_jsonl(
            data_dir / "metrics.jsonl",
            {
                "timestamp": str(tick),
                "event_type": "metrics",
                "payload": {
                    "tick": tick,
                    "score": 0.5,
                    "novelty": 0.2,
                    "diversity": 0.2,
                    "efficiency": 0.6,
                },
            },
        )
    state = replay_state(str(data_dir))
    pressures = compute_pressures(state)
    quest = generate_quest(pressures, state, tick=state.tick + 1)
    assert quest["quest_type"] in {"exploration", "meta"}


def test_pressure_vector_generation(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    ensure_spine(data_dir)
    for tick in range(1, 4):
        append_jsonl(
            data_dir / "metrics.jsonl",
            {
                "timestamp": str(tick),
                "event_type": "metrics",
                "payload": {"tick": tick, "score": 0.4, "novelty": 0.1, "diversity": 0.1, "efficiency": 0.2},
            },
        )
        append_event("cycle_completed", {"tick": tick, "best_score": 0.4, "supervisor_mode": "normal"}, data_dir=data_dir)
    pressures = compute_pressures(replay_state(str(data_dir)))
    assert set(pressures) == {
        "novelty_pressure",
        "diversity_pressure",
        "efficiency_pressure",
        "repair_pressure",
        "domain_shift_pressure",
        "reframing_pressure",
    }


def test_quest_regeneration(tmp_path: Path) -> None:
    quest_path = tmp_path / "state" / "quest.json"
    original = ensure_quest(1, pressure_vector={"novelty_pressure": 0.1}, plateau_streak=0, path=str(quest_path))[0]
    original["ttl_ticks"] = 1
    from core.quest import save_quest

    save_quest(original, str(quest_path))
    regenerated, changed = ensure_quest(3, pressure_vector={"novelty_pressure": 0.9}, plateau_streak=2, path=str(quest_path))
    assert changed is True
    assert regenerated["id"] != original["id"]


def test_supervisor_safe_mode_path_does_not_crash(tmp_path: Path) -> None:
    class FlakyAdapter(KernelAdapter):
        def __init__(self) -> None:
            super().__init__(
                data_dir=tmp_path / "data",
                artifact_dir=tmp_path / "artifact_store",
                state_dir=tmp_path / "state",
            )
            self.calls = 0

        def execute_cycle(self, **kwargs):  # type: ignore[override]
            self.calls += 1
            if self.calls <= 2:
                raise RuntimeError("boom")
            return {
                "tick": kwargs["tick"],
                "best_score": 0.4,
                "metrics": {"score": 0.4},
                "artifact_ids": [],
                "population_size": 1,
            }

    adapter = FlakyAdapter()
    supervisor = Supervisor(adapter)
    state = replay_state(str(tmp_path / "data"))
    report = supervisor.run_cycle(state)
    assert report["supervisor_mode"] == "safe_mode"
    assert report["best_score"] == 0.4
