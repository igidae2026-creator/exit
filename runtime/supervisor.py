from __future__ import annotations

from typing import Any, Callable

from artifact.runtime_store import ArtifactStore, create_artifact
from genesis.event_log import append_jsonl
from genesis.logger import AppendOnlyLogger, log_event
from runtime.evolve import archive_pressure_hook, policy_evolution_hook, selection, signal
from runtime.kernel_adapter import KernelAdapter
from runtime.policy_store import PolicyRuntime
from runtime.pressure_engine import compute_pressures
from runtime.quest_ecology import generate_quest_portfolio
from runtime.quota_policy import allocate_quota
from runtime.replay_state import archive_pressure
from runtime.quest_manager import QuestManager, reframing_triggers
from validation.immutability import validate_constitution


class Supervisor:
    def __init__(self, adapter: KernelAdapter, *, total_budget: float = 100.0) -> None:
        self.adapter = adapter
        self.total_budget = total_budget
        self.mode = "normal"
        self.logger = AppendOnlyLogger(log_dir=self.adapter.data_dir)
        self.artifact_store = ArtifactStore(store_dir=self.adapter.artifact_dir, logger=self.logger, log_dir=self.adapter.data_dir)
        self.policy_runtime = PolicyRuntime(self.artifact_store, self.logger)
        self.quest_manager = QuestManager(max_selected=3)
        self._hydrated = False

    def validate(self) -> dict[str, Any]:
        summary = self.adapter.validate()
        replay_summary = self.adapter.checkpoint_restore()
        log_event("supervisor_validate", {"summary": summary, "checkpoint": replay_summary}, data_dir=self.adapter.data_dir)
        return {
            **summary,
            "replayable": True,
            "policy_names": sorted(self.policy_runtime.current_policy_ids()),
        }

    def _archive_append(self, name: str, payload: dict[str, Any]) -> None:
        append_jsonl(self.adapter.archive_dir / f"{name}.jsonl", payload)

    def retry_once(self, func: Callable[[], dict[str, Any]], *, tick: int) -> dict[str, Any]:
        try:
            return func()
        except Exception as exc:
            self.logger.log_event("supervisor_action", {"hook": "retry_once", "tick": tick, "error": str(exc)})
            self.logger.log_event("repair_attempt", {"tick": tick, "reason": "retry_once", "error": str(exc)})
            try:
                return func()
            except Exception as retry_exc:
                self.mode = "safe_mode"
                self.logger.log_event("repair_failed", {"tick": tick, "reason": "retry_once", "error": str(retry_exc)})
                repair_artifact = create_artifact(
                    "repair",
                    {"reason": "retry_once_exhausted", "error": str(retry_exc), "mode": self.mode},
                    parent_ids=[],
                    domain=self.adapter.domain_name,
                    source="supervisor",
                    tick=tick,
                    artifact_dir=self.adapter.artifact_dir,
                    data_dir=self.adapter.data_dir,
                )
                return {
                    "tick": tick,
                    "best_score": 0.0,
                    "best_artifact_id": repair_artifact.artifact_id,
                    "population": [],
                    "population_size": 1,
                    "candidate_rows": [],
                    "metrics": {},
                    "artifact_ids": [repair_artifact.artifact_id],
                }

    def _hydrate_from_replay(self, replay_state: object) -> None:
        if self._hydrated:
            return
        current_policies = dict(getattr(replay_state, "current_policies", {}) or {})
        if current_policies:
            self.policy_runtime.restore_current(current_policies)
        quest_rows = list(getattr(replay_state, "quests", {}).values() or [])
        if quest_rows:
            self.quest_manager.import_quests(quest_rows)
        self._hydrated = True

    def checkpoint_restore(self) -> dict[str, Any]:
        restored = self.adapter.checkpoint_restore()
        self.logger.log_event("supervisor_action", {"hook": "checkpoint_restore", "tick": int(restored.get("tick", 0) or 0), "best_score": float(restored.get("best_score", 0.0) or 0.0)})
        return restored

    def safe_mode(self, *, tick: int, reason: str, parent_ids: list[str]) -> dict[str, Any]:
        self.mode = "safe_mode"
        self.logger.log_event("supervisor_action", {"hook": "safe_mode", "tick": tick, "reason": reason, "mode": "safe_mode"})
        repair_artifact = create_artifact(
            "repair",
            {"reason": reason, "mode": "safe_mode"},
            parent_ids=parent_ids,
            domain=self.adapter.domain_name,
            source="supervisor",
            tick=tick,
            artifact_dir=self.adapter.artifact_dir,
            data_dir=self.adapter.data_dir,
        )
        return {
            "quota": {"worker_budget": 1.0, "mutation_budget": 12.0, "repair_budget": 42.0, "exploration_budget": 18.0, "replay_budget": 28.0},
            "repair_artifact_id": repair_artifact.artifact_id,
        }

    def quota_downshift(self, quota: dict[str, float], *, tick: int) -> dict[str, float]:
        downshifted = {key: round(value * 0.5, 6) for key, value in quota.items()}
        self.mode = "quota_downshift"
        self.logger.log_event("supervisor_action", {"hook": "quota_downshift", "tick": tick, "mode": self.mode, "before": quota, "after": downshifted})
        return downshifted

    @staticmethod
    def _portfolio_signature(item: dict[str, Any]) -> tuple[str, str, str, str]:
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        source_payload = item.get("source_payload") if isinstance(item.get("source_payload"), dict) else {}
        quest_type = str(item.get("quest_type") or metadata.get("quest_type") or source_payload.get("quest_type") or "work_quest")
        domain = str(item.get("domain") or metadata.get("domain") or source_payload.get("domain") or "")
        title = str(item.get("title") or "")
        description = str(item.get("description") or "")
        return (quest_type, domain, title, description)

    def _sync_quests(self, portfolio: list[dict[str, Any]], tick: int) -> list[dict[str, Any]]:
        existing_active = [*self.quest_manager.list("selected"), *self.quest_manager.list("proposed")]
        active_by_signature = {self._portfolio_signature(quest.to_dict()): quest for quest in existing_active}
        active: list[dict[str, Any]] = []
        retained_ids: set[str] = set()
        for item in portfolio:
            quest_type = str(item.get("quest_type") or "work_quest")
            signature = self._portfolio_signature(item)
            quest = active_by_signature.get(signature)
            if quest is None:
                quest = self.quest_manager.propose(
                    title=str(item.get("title") or quest_type),
                    description=str(item.get("description") or quest_type),
                    source="pressure",
                    priority=0.9 if quest_type == "reframing_quest" else 0.6,
                    source_payload=item,
                    metadata={"quest_type": quest_type, "tick": tick, "domain": item.get("domain")},
                )
                self.logger.log_event("quest_proposed", {"quest_id": quest.quest_id, "quest": quest.to_dict()})
            retained_ids.add(quest.quest_id)
            active.append(quest.to_dict())
        for quest in existing_active:
            if quest.quest_id in retained_ids:
                continue
            retired = self.quest_manager.retire(quest.quest_id, reason="portfolio_refresh")
            self.logger.log_event("quest_retired", {"quest_id": retired.quest_id, "quest": retired.to_dict()})
        selected: list[dict[str, Any]] = []
        for quest in self.quest_manager.list("selected"):
            if quest.quest_id in retained_ids:
                selected.append(quest.to_dict())
        while len(self.quest_manager.list("selected")) < self.quest_manager.max_selected:
            next_quest = self.quest_manager.select_next()
            if not next_quest:
                break
            self.logger.log_event("quest_selected", {"quest_id": next_quest.quest_id, "quest": next_quest.to_dict()})
            selected.append(next_quest.to_dict())
        return selected or active[: self.quest_manager.max_selected]

    def run_cycle(self, replay_state: object) -> dict[str, Any]:
        validate_constitution()
        self._hydrate_from_replay(replay_state)
        tick = int(getattr(replay_state, "tick", 0) or 0) + 1
        self.mode = "normal"
        checkpoint = self.checkpoint_restore()

        signal_payload = signal(replay_state)
        pressures = compute_pressures(replay_state)
        archive_vector = archive_pressure(replay_state)
        pressures.update({key: value for key, value in archive_vector.items() if key not in pressures})
        self.logger.log_event("pressure_snapshot", pressures)
        self._archive_append("pressure_snapshots", {"tick": tick, **pressures})

        portfolio = generate_quest_portfolio(replay_state, pressures, max_quests=3)
        reasons = reframing_triggers(
            novelty_history=[row.get("novelty", 0.0) for row in getattr(replay_state, "metric_history", [])],
            diversity_history=[row.get("diversity", 0.0) for row in getattr(replay_state, "metric_history", [])],
            score_history=[row.get("score", 0.0) for row in getattr(replay_state, "metric_history", [])],
            repair_failures=len([row for row in getattr(replay_state, "repairs", []) if row.get("event_type") == "repair_failed"]),
            lineage_share=float(getattr(replay_state, "lineage_concentration", lambda: 0.0)() if hasattr(replay_state, "lineage_concentration") else 0.0),
            repeated_low_diversity_cycles=int(getattr(replay_state, "plateau_streak", 0) or 0),
        )
        if reasons:
            portfolio.insert(0, {"quest_type": "reframing_quest", "title": "Reframe exploration", "description": ", ".join(reasons), "domain": self.adapter.domain_name})
        if not portfolio:
            portfolio = [{"quest_type": "work_quest", "title": "Work quest", "description": "Exploit the best current strategy in the canonical domain.", "domain": self.adapter.domain_name}]
        active_quests = self._sync_quests(portfolio[:3], tick)
        self.logger.log_event("quest_portfolio", {"tick": tick, "quests": active_quests})
        for quest in active_quests:
            self._archive_append("quests", {"tick": tick, **quest})

        selection_policy = policy_evolution_hook(replay_state, pressures)
        mutation_policy = {
            **self.policy_runtime.get_policy("mutation_policy"),
            "exploration_bias": round(0.30 + (0.50 * float(pressures.get("novelty_pressure", 0.0))), 6),
            "repair_bias": round(0.20 + (0.50 * float(pressures.get("repair_pressure", 0.0))), 6),
        }
        quest_policy = {
            **self.policy_runtime.get_policy("quest_policy"),
            "metric_threshold": round(0.50 - (0.10 * float(pressures.get("reframing_pressure", 0.0))), 6),
        }
        evaluation_policy = {
            **self.policy_runtime.get_policy("evaluation_policy"),
            "minimum_score": round(0.40 + (0.10 * float(pressures.get("usefulness_pressure", 0.0))), 6),
        }
        repair_policy = {
            **self.policy_runtime.get_policy("repair_policy"),
            "safe_mode_after": 2 if float(pressures.get("repair_pressure", 0.0)) >= 0.7 else 3,
        }
        quota_policy = {
            **self.policy_runtime.get_policy("quota_policy"),
            "base_worker_budget": 2 + int(round(float(pressures.get("transfer_pressure", 0.0)) * 2)),
        }
        policy_bundle = {
            "selection_policy": selection_policy,
            "mutation_policy": mutation_policy,
            "quest_policy": quest_policy,
            "evaluation_policy": evaluation_policy,
            "repair_policy": repair_policy,
            "quota_policy": quota_policy,
        }
        policy_record_ids = {name: self.policy_runtime.register_policy(name, definition, activate=True) for name, definition in policy_bundle.items()}
        policy = {**selection_policy, **mutation_policy, **quest_policy, **evaluation_policy, **repair_policy, **quota_policy}
        quota = allocate_quota(pressures, base_budget=self.total_budget)
        self.logger.log_event("quota_decision", quota)
        self._archive_append("quota_decisions", {"tick": tick, **quota})
        self._archive_append("policies", {"tick": tick, "artifacts": policy_record_ids, **policy_bundle})
        self._archive_append("domain_genomes", {"tick": tick, **self.adapter.domain_genome.to_dict()})
        self.logger.log_event("domain_genome_loaded", {"tick": tick, **self.adapter.domain_genome.to_dict()})

        selected = selection(replay_state)
        parent_ids = list(selected.get("parent_ids", []))
        transfer_strategy = None
        artifacts = getattr(replay_state, "artifacts", {}) or {}
        if parent_ids:
            transfer_strategy = ((artifacts.get(parent_ids[0]) or {}).get("payload") or {}).get("strategy")

        safe_bundle = None
        if float(pressures.get("repair_pressure", 0.0)) >= 0.8:
            safe_bundle = self.safe_mode(tick=tick, reason="repair_pressure", parent_ids=parent_ids)
            quota = self.quota_downshift(dict(safe_bundle["quota"]), tick=tick)
        elif float(pressures.get("reframing_pressure", 0.0)) >= 0.7:
            self.logger.log_event("supervisor_action", {"hook": "reframing_quest_injection", "tick": tick, "mode": self.mode})

        def _run() -> dict[str, Any]:
            return self.adapter.execute_cycle(
                tick=tick,
                quests=active_quests,
                policy=policy,
                quota=quota,
                parent_ids=parent_ids,
                safe_mode=self.mode == "safe_mode",
                transfer_strategy=transfer_strategy,
            )

        result = self.retry_once(_run, tick=tick)
        best_metrics = dict(result.get("metrics", {}))
        supervisor_mode = self.mode
        if float(getattr(replay_state, "lineage_concentration", lambda: 0.0)() if hasattr(replay_state, "lineage_concentration") else 0.0) >= 0.68:
            supervisor_mode = "anti_collapse_guard"
            self.logger.log_event("supervisor_action", {"hook": "anti_collapse_guard", "tick": tick, "mode": supervisor_mode})

        report = {
            "tick": tick,
            "signal": signal_payload,
            "pressures": pressures,
            "quota": quota,
            "policy": policy,
            "active_quests": active_quests,
            "best_score": float(result.get("best_score", 0.0) or 0.0),
            "best_artifact_id": str(result.get("best_artifact_id") or checkpoint.get("best_artifact_id") or ""),
            "metrics": best_metrics,
            "artifact_ids": list(result.get("artifact_ids", [])),
            "population_size": int(result.get("population_size", 0) or 0),
            "supervisor_mode": supervisor_mode,
            "archive": archive_pressure_hook(replay_state),
        }
        self.logger.log_event("tick_completed", report)
        return report
