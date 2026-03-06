from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from artifact.lineage import lineage_concentration
from core.artifact import ArtifactStore, create_artifact
from core.kernel_adapter import KernelAdapter
from core.log import AppendOnlyLogger
from core.policy import PolicyRuntime
from core.replay import archive_pressure, replay_state
from core.strategy_genome import StrategyGenome
from core.supervisor import Supervisor
from runtime.orchestrator import Orchestrator, OrchestratorConfig
from runtime.quest_manager import QuestManager, reframing_triggers


class ExplorationCivilizationTests(unittest.TestCase):
    def test_lineage_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            artifact_dir = Path(tmp) / "artifact_store"
            create_artifact("strategy", {"value": 1}, tick=1, artifact_dir=artifact_dir, data_dir=data_dir, metadata={"lineage_id": "lineage-a"})
            create_artifact("strategy", {"value": 2}, tick=2, artifact_dir=artifact_dir, data_dir=data_dir, metadata={"lineage_id": "lineage-b"})
            create_artifact("strategy", {"value": 3}, tick=3, artifact_dir=artifact_dir, data_dir=data_dir, metadata={"lineage_id": "lineage-b"})
            state = replay_state(data_dir, state_dir=Path(tmp) / "state", archive_dir=Path(tmp) / "archive")
            self.assertEqual(state.lineages["lineage-a"], 1)
            self.assertEqual(state.lineages["lineage-b"], 2)
            self.assertGreaterEqual(lineage_concentration(str(data_dir)), 2 / 3)
            self.assertGreaterEqual(archive_pressure(state)["lineage_concentration"], 2 / 3)

    def test_reframing_quest_trigger(self) -> None:
        reasons = reframing_triggers(
            novelty_history=[0.2, 0.2, 0.18, 0.19],
            diversity_history=[0.3, 0.28, 0.27, 0.26],
            score_history=[0.5, 0.49, 0.5, 0.5],
            repair_failures=3,
            lineage_share=0.8,
            repeated_low_diversity_cycles=4,
        )
        self.assertIn("novelty_collapse", reasons)
        self.assertIn("lineage_concentration", reasons)
        manager = QuestManager()
        quest = manager.generate_reframing_quest(reasons=reasons, lineage_share=0.8)
        self.assertEqual(quest.metadata["quest_type"], "reframing_quest")

    def test_policy_swap_safety(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            store_dir = Path(tmp) / "artifact_store"
            logger = AppendOnlyLogger(data_dir)
            store = ArtifactStore(store_dir=store_dir, logger=logger, log_dir=data_dir)
            runtime = PolicyRuntime(store, logger)
            artifact_id = runtime.register_policy("selection_policy", {"diversity_bias": 0.9, "dominance_threshold": 0.6})
            definition = runtime.swap_policy("selection_policy", artifact_id)
            self.assertEqual(definition["diversity_bias"], 0.9)
            self.assertEqual(runtime.get_policy("selection_policy")["dominance_threshold"], 0.6)

    def test_quota_allocator_and_orchestrator_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = OrchestratorConfig(tick_seconds=0.0, max_ticks=4, data_dir=Path(tmp) / "data", artifact_store_dir=Path(tmp) / "artifact_store", state_dir=Path(tmp) / "state", archive_dir=Path(tmp) / "archive")
            orchestrator = Orchestrator(config)
            reports = orchestrator.run(max_ticks=4)
            self.assertEqual(len(reports), 4)
            self.assertTrue(any(len(report["active_quests"]) >= 1 for report in reports))
            self.assertTrue(any(len(set(report["signal"].keys())) >= 3 for report in reports))
            replay = orchestrator.replay()
            self.assertGreaterEqual(replay["tick"], 4)

    def test_cli_validate_replay_and_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_root = Path(tmp) / ".metaos_runtime"
            env = os.environ.copy()
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            env["METAOS_RUNTIME_ROOT"] = str(runtime_root)
            env["METAOS_TICK_SECONDS"] = "0"
            env["METAOS_MAX_TICKS"] = "3"
            run = subprocess.run([sys.executable, "run_metaos.py"], cwd=Path(__file__).resolve().parents[1], env=env, capture_output=True, text=True, check=False, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)
            validate = subprocess.run([sys.executable, "-m", "metaos.cli", "validate"], cwd=Path(__file__).resolve().parents[1], env=env, capture_output=True, text=True, check=False, timeout=30)
            self.assertEqual(validate.returncode, 0, validate.stderr)
            replay_cmd = subprocess.run([sys.executable, "-m", "metaos.cli", "replay"], cwd=Path(__file__).resolve().parents[1], env=env, capture_output=True, text=True, check=False, timeout=30)
            self.assertEqual(replay_cmd.returncode, 0, replay_cmd.stderr)
            payload = json.loads(replay_cmd.stdout)
            self.assertGreaterEqual(payload["tick"], 3)
            self.assertTrue(payload["domains"])

    def test_execute_cycle_shares_lineage_id_across_candidate_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            adapter = KernelAdapter(
                data_dir=Path(tmp) / "data",
                artifact_dir=Path(tmp) / "artifact_store",
                state_dir=Path(tmp) / "state",
                archive_dir=Path(tmp) / "archive",
            )
            result = adapter.execute_cycle(
                tick=1,
                quests=[{"id": "q1", "domain": "code_domain"}],
                policy={"mutation_scale": 0.0},
                quota={"worker_budget": 2},
                parent_ids=["parent-lineage"],
            )
            state = replay_state(adapter.data_dir, state_dir=adapter.state_dir, archive_dir=adapter.archive_dir)
            for row in result["candidate_rows"]:
                lineage_ids = {
                    str((state.artifacts[artifact_id].get("metadata") or {}).get("lineage_id"))
                    for artifact_id in row["artifact_ids"]
                }
                self.assertEqual(lineage_ids, {"parent-lineage"})

    def test_sync_quests_preserves_hydrated_selected_quest_when_portfolio_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            adapter = KernelAdapter(
                data_dir=Path(tmp) / "data",
                artifact_dir=Path(tmp) / "artifact_store",
                state_dir=Path(tmp) / "state",
                archive_dir=Path(tmp) / "archive",
            )
            supervisor = Supervisor(adapter)
            replay = type(
                "ReplayStub",
                (),
                {
                    "current_policies": {},
                    "quests": {
                        "q_existing": {
                            "quest_id": "q_existing",
                            "title": "Work quest",
                            "description": "Exploit the best current strategy in the canonical domain.",
                            "source": "pressure",
                            "state": "selected",
                            "priority": 0.6,
                            "source_payload": {
                                "quest_type": "work_quest",
                                "title": "Work quest",
                                "description": "Exploit the best current strategy in the canonical domain.",
                                "domain": "code_domain",
                            },
                            "metadata": {"quest_type": "work_quest", "tick": 1, "domain": "code_domain"},
                        }
                    },
                },
            )()
            supervisor._hydrate_from_replay(replay)
            selected = supervisor._sync_quests(
                [
                    {
                        "quest_type": "work_quest",
                        "title": "Work quest",
                        "description": "Exploit the best current strategy in the canonical domain.",
                        "domain": "code_domain",
                    }
                ],
                tick=2,
            )
            self.assertEqual([quest["quest_id"] for quest in selected], ["q_existing"])
            self.assertEqual(supervisor.quest_manager.get("q_existing").state, "selected")


if __name__ == "__main__":
    unittest.main()
