from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.artifact import create_artifact
from core.event_log import append_event, append_jsonl, ensure_spine
from core.kernel_adapter import KernelAdapter
from core.quest import ensure_quest, save_quest
from core.replay import replay_state
from core.supervisor import Supervisor
from evolution.pressure_engine import compute_pressures
from evolution.quest_ecology import generate_quest_portfolio
from unittest.mock import Mock


class CivilizationMvpTests(unittest.TestCase):
    def test_append_only_invariant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            ensure_spine(data_dir)
            events_path = data_dir / "events.jsonl"
            before = events_path.stat().st_size
            append_event("alpha", {"tick": 1}, data_dir=data_dir)
            middle = events_path.stat().st_size
            append_event("beta", {"tick": 2}, data_dir=data_dir)
            after = events_path.stat().st_size
            self.assertLessEqual(before, middle)
            self.assertLess(middle, after)

    def test_replay_reconstructs_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            artifact_dir = Path(tmp) / "artifact_store"
            ensure_spine(data_dir)
            create_artifact("policy", {"selection_bias": "novelty"}, tick=1, artifact_dir=artifact_dir, data_dir=data_dir)
            append_event("cycle_completed", {"tick": 1, "best_score": 0.7, "supervisor_mode": "normal"}, data_dir=data_dir)
            state = replay_state(data_dir, state_dir=Path(tmp) / "state", archive_dir=Path(tmp) / "archive")
            self.assertEqual(state.tick, 1)
            self.assertGreaterEqual(state.best_score, 0.7)
            self.assertEqual(state.artifacts_by_kind["policy"], 1)

    def test_plateau_causes_exploration_or_reframing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            ensure_spine(data_dir)
            for tick in range(1, 5):
                append_event("cycle_completed", {"tick": tick, "best_score": 0.5, "supervisor_mode": "normal"}, data_dir=data_dir)
                append_jsonl(data_dir / "metrics.jsonl", {"timestamp": str(tick), "event_type": "metrics", "payload": {"tick": tick, "score": 0.5, "novelty": 0.2, "diversity": 0.2, "efficiency": 0.6, "usefulness": 0.4, "persistence": 0.4, "recombination": 0.4}})
            state = replay_state(data_dir, state_dir=Path(tmp) / "state", archive_dir=Path(tmp) / "archive")
            pressures = compute_pressures(state)
            portfolio = generate_quest_portfolio(state, pressures, max_quests=3)
            quest_types = {quest["quest_type"] for quest in portfolio}
            self.assertTrue({"exploration_quest", "reframing_quest"} & quest_types)

    def test_quest_regeneration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            quest_path = Path(tmp) / "state" / "quest.json"
            original = ensure_quest(1, pressure_vector={"novelty_pressure": 0.1}, plateau_streak=0, path=str(quest_path))[0]
            original["ttl_ticks"] = 1
            save_quest(original, str(quest_path))
            regenerated, changed = ensure_quest(3, pressure_vector={"novelty_pressure": 0.9, "reframing_pressure": 0.9}, plateau_streak=3, path=str(quest_path))
            self.assertTrue(changed)
            self.assertNotEqual(regenerated["id"], original["id"])
            self.assertIn(regenerated["quest_type"], {"exploration", "reframing"})

    def test_supervisor_safe_mode_path_does_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            adapter = KernelAdapter(data_dir=Path(tmp) / "data", artifact_dir=Path(tmp) / "artifact_store", state_dir=Path(tmp) / "state", archive_dir=Path(tmp) / "archive")
            supervisor = Supervisor(adapter)
            state = replay_state(adapter.data_dir, state_dir=adapter.state_dir, archive_dir=adapter.archive_dir)
            append_event("repair_failed", {"tick": 1}, data_dir=adapter.data_dir)
            append_event("repair_failed", {"tick": 2}, data_dir=adapter.data_dir)
            append_event("repair_failed", {"tick": 3}, data_dir=adapter.data_dir)
            state = replay_state(adapter.data_dir, state_dir=adapter.state_dir, archive_dir=adapter.archive_dir)
            report = supervisor.run_cycle(state)
            self.assertIn(report["supervisor_mode"], {"safe_mode", "quota_downshift", "anti_collapse_guard", "normal"})
            self.assertGreaterEqual(report["population_size"], 1)

    def test_replay_bootstraps_domain_and_quest_when_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            state = replay_state(data_dir, state_dir=Path(tmp) / "state", archive_dir=Path(tmp) / "archive")
            self.assertIn("code_domain", state.domain_counts)
            self.assertTrue(state.quest_portfolio)

    def test_retry_once_falls_back_to_repair_artifact_after_second_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            adapter = KernelAdapter(data_dir=Path(tmp) / "data", artifact_dir=Path(tmp) / "artifact_store", state_dir=Path(tmp) / "state", archive_dir=Path(tmp) / "archive")
            supervisor = Supervisor(adapter)
            failing = Mock(side_effect=RuntimeError("boom"))
            result = supervisor.retry_once(failing, tick=1)
            self.assertEqual(failing.call_count, 2)
            self.assertTrue(result["artifact_ids"])
            self.assertEqual(result["population_size"], 1)


if __name__ == "__main__":
    unittest.main()
