from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.artifact import ArtifactStore
from core.log import AppendOnlyLogger
from core.policy import PolicyRuntime
from core.replay import archive_pressure, rebuild_runtime_state
from core.strategy_genome import StrategyGenome
from runtime.economy_controller import QuotaAllocator
from runtime.orchestrator import Orchestrator, OrchestratorConfig
from runtime.quest_manager import QuestManager, reframing_triggers


class ExplorationCivilizationTests(unittest.TestCase):
    def test_append_only_invariant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            logger = AppendOnlyLogger(Path(tmp) / "data")
            logger.log_event("alpha", {"value": 1})
            size1 = (Path(tmp) / "data" / "events.jsonl").stat().st_size
            logger.log_event("beta", {"value": 2})
            size2 = (Path(tmp) / "data" / "events.jsonl").stat().st_size
            self.assertGreater(size2, size1)
            records = list(logger.replay_events())
            self.assertEqual([record.event_type for record in records], ["alpha", "beta"])

    def test_replay_reconstructs_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            store_dir = Path(tmp) / "artifact_store"
            logger = AppendOnlyLogger(data_dir)
            store = ArtifactStore(store_dir=store_dir, logger=logger, log_dir=data_dir)
            runtime = PolicyRuntime(store, logger)
            runtime.register_policy("quota_policy", {"minimum_worker_budget": 2, "base_worker_budget": 3}, activate=True)
            genome = StrategyGenome.create(domain="canonical_domain", eval_axes={"quality": 1.0}, budget=0.2)
            store.create_json_artifact(
                {"strategy_genome": genome.to_dict()},
                metadata={"artifact_type": "strategy_genome", "lineage_id": "lineage-a", "parent_lineage": "lineage-a"},
            )
            logger.log_metric("metrics", {"quality": 0.7, "novelty": 0.3, "diversity": 0.4, "efficiency": 0.6, "cost": 0.7, "score": 0.54})
            manager = QuestManager()
            quest = manager.generate_reframing_quest(reasons=["novelty_collapse"], lineage_share=0.8)
            logger.log_event("quest_proposed", {"quest_id": quest.quest_id, "quest": quest.to_dict()})
            logger.log_event("repair_failed", {"tick": 1})
            logger.log_event("pressure_snapshot", {"exploration": 0.7, "repair": 0.5, "diversity": 0.8, "replay": 0.2, "collapse": 0.1})
            logger.log_event("quota_decision", {"mutation_budget": 0.2, "exploration_budget": 0.3, "repair_budget": 0.2, "replay_budget": 0.1, "worker_budget": 2})

            replay = rebuild_runtime_state(data_dir)
            self.assertIn("quota_policy", replay.current_policies)
            self.assertEqual(replay.lineages["lineage-a"], 1)
            self.assertEqual(len(replay.metrics_history), 1)
            self.assertIn(quest.quest_id, replay.quests)
            self.assertEqual(len(replay.quota_decisions), 1)

    def test_lineage_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            store_dir = Path(tmp) / "artifact_store"
            logger = AppendOnlyLogger(data_dir)
            store = ArtifactStore(store_dir=store_dir, logger=logger, log_dir=data_dir)
            for lineage_id in ("lineage-a", "lineage-b", "lineage-b"):
                genome = StrategyGenome.create(domain="canonical_domain", eval_axes={"quality": 1.0}, budget=0.1)
                store.create_json_artifact(
                    {"strategy_genome": genome.to_dict()},
                    metadata={"artifact_type": "strategy_genome", "lineage_id": lineage_id, "parent_lineage": lineage_id},
                )
            replay = rebuild_runtime_state(data_dir)
            self.assertEqual(replay.lineages["lineage-a"], 1)
            self.assertEqual(replay.lineages["lineage-b"], 2)
            pressure = archive_pressure(replay)
            self.assertGreaterEqual(pressure["lineage_concentration"], 2 / 3)

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
        self.assertIn("summary", quest.metadata["framing"])

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

    def test_quota_allocator_output(self) -> None:
        allocator = QuotaAllocator(total_budget=1.0, base_workers=2)
        quotas = allocator.allocate({"exploration": 0.7, "repair": 0.3, "diversity": 0.6, "replay": 0.2, "collapse": 0.1})
        self.assertEqual(set(quotas), {"mutation_budget", "exploration_budget", "repair_budget", "replay_budget", "worker_budget"})
        self.assertIsInstance(quotas["worker_budget"], int)
        self.assertGreater(quotas["exploration_budget"], quotas["replay_budget"])

    def test_anti_collapse_multi_lineage_survival(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = OrchestratorConfig(tick_seconds=0.0, max_ticks=1, data_dir=Path(tmp) / "data", artifact_store_dir=Path(tmp) / "artifact_store")
            orchestrator = Orchestrator(config)
            selected = orchestrator._select_lineage({"lineage-a": 10, "lineage-b": 1}, "lineage-a", anti_collapse=True)
            self.assertEqual(selected, "lineage-b")

    def test_supervisor_safe_mode_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = OrchestratorConfig(tick_seconds=0.0, max_ticks=1, data_dir=Path(tmp) / "data", artifact_store_dir=Path(tmp) / "artifact_store")
            orchestrator = Orchestrator(config)
            orchestrator.state["repair_failures"] = 3
            orchestrator.state["quotas"] = {"mutation_budget": 0.2, "exploration_budget": 0.4, "repair_budget": 0.3, "replay_budget": 0.1, "worker_budget": 3}
            ctx = {
                "errors": [],
                "stage_results": {
                    "signal": {"pressure": {"lineage_concentration": 0.3}},
                    "strategy": {"target_lineage": "lineage-a"},
                    "mutation": {"allow_retry": False},
                    "quest": {"reasons": []},
                    "metrics": {"score": 0.2},
                },
            }
            decision = orchestrator.decision(ctx)
            self.assertTrue(orchestrator.state["safe_mode"])
            self.assertIn("safe_mode", decision["actions"])
            self.assertEqual(orchestrator.state["quotas"]["worker_budget"], 1)


if __name__ == "__main__":
    unittest.main()
