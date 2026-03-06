from __future__ import annotations

from typing import Any, Callable
from pathlib import Path

from core.artifact import create_artifact
from core.constitution_guard import validate_constitution
from core.event_log import append_jsonl
from core.kernel_adapter import KernelAdapter
from core.log import log_event
from evolution.evolve import archive_pressure_hook, mutation, policy_evolution_hook, selection, signal
from evolution.pressure_engine import compute_pressures
from evolution.quest_ecology import choose_quest_kind, quest_payload
from evolution.quest_generator import generate_quest
from evolution.quota_allocator import allocate_quota


class Supervisor:
    def __init__(self, adapter: KernelAdapter, *, total_budget: float = 100.0) -> None:
        self.adapter = adapter
        self.total_budget = total_budget
        self.mode = "normal"

    def validate(self) -> dict[str, Any]:
        validate_constitution()
        self.adapter.archive_dir.mkdir(parents=True, exist_ok=True)
        summary = self.adapter.validate()
        log_event("supervisor_validate", summary, data_dir=str(self.adapter.data_dir))
        return summary

    def _archive_append(self, name: str, payload: dict[str, Any]) -> None:
        append_jsonl(self.adapter.archive_dir / f"{name}.jsonl", payload)

    def retry_once(self, func: Callable[[], dict[str, Any]], *, tick: int) -> dict[str, Any]:
        try:
            return func()
        except Exception as exc:
            log_event("supervisor_retry_once", {"tick": tick, "error": str(exc)}, data_dir=str(self.adapter.data_dir))
            return func()

    def checkpoint_restore(self) -> dict[str, Any]:
        restored = self.adapter.checkpoint_restore()
        log_event(
            "supervisor_checkpoint_restore",
            {"tick": restored.get("tick", 0), "best_score": restored.get("best_score", 0.0)},
            data_dir=str(self.adapter.data_dir),
        )
        return restored

    def safe_mode(self, *, tick: int, reason: str, parent_ids: list[str]) -> dict[str, Any]:
        self.mode = "safe_mode"
        log_event("safe_mode_entered", {"tick": tick, "reason": reason}, data_dir=str(self.adapter.data_dir))
        repair_artifact = create_artifact(
            "repair",
            {"reason": reason, "mode": "safe_mode"},
            parent_ids=parent_ids,
            domain=self.adapter.domain_name,
            source="supervisor",
            tick=tick,
            artifact_dir=self.adapter.artifact_dir,
            data_dir=str(self.adapter.data_dir),
        )
        return {
            "quota": {"exploit": 20.0, "explore": 5.0, "recovery": 60.0, "mutation": 5.0},
            "repair_artifact_id": repair_artifact.artifact_id,
        }

    def quota_downshift(self, quota: dict[str, float], *, tick: int) -> dict[str, float]:
        downshifted = {key: round(value * 0.5, 6) for key, value in quota.items()}
        self.mode = "quota_downshift"
        log_event("quota_downshift", {"tick": tick, "before": quota, "after": downshifted}, data_dir=str(self.adapter.data_dir))
        return downshifted

    def run_cycle(self, replay_state: object) -> dict[str, Any]:
        tick = int(getattr(replay_state, "tick", 0) or 0) + 1
        self.mode = "normal"
        self.validate()
        checkpoint = self.checkpoint_restore()

        signal_payload = signal(replay_state)
        pressures = compute_pressures(replay_state)
        quest = generate_quest(pressures, replay_state, domain_hint=self.adapter.domain_name, tick=tick)
        quest_kind = choose_quest_kind(replay_state, pressures, data_dir=str(self.adapter.data_dir))
        quest.update(quest_payload(quest_kind, pressures))
        parent_ids = selection(replay_state)["parent_ids"]

        quest_artifact = create_artifact(
            "quest",
            quest,
            parent_ids=parent_ids,
            domain=self.adapter.domain_name,
            quest_id=str(quest.get("id") or ""),
            source="supervisor",
            tick=tick,
            artifact_dir=self.adapter.artifact_dir,
            data_dir=str(self.adapter.data_dir),
        )
        log_event("quest_selected", {"tick": tick, "quest": quest}, data_dir=str(self.adapter.data_dir))
        self._archive_append("quests", {"tick": tick, **quest})

        policy = policy_evolution_hook(replay_state, pressures)
        policy_artifact = create_artifact(
            "policy",
            policy,
            parent_ids=[quest_artifact.artifact_id, *parent_ids],
            domain=self.adapter.domain_name,
            quest_id=str(quest.get("id") or ""),
            source="supervisor",
            tick=tick,
            artifact_dir=self.adapter.artifact_dir,
            data_dir=str(self.adapter.data_dir),
        )
        log_event("policy_evolved", {"tick": tick, "policy": policy}, data_dir=str(self.adapter.data_dir))
        self._archive_append("policies", {"tick": tick, **policy})
        self._archive_append("domain_genomes", {"tick": tick, "adapter": self.adapter.domain_genome.adapter, "constraints": self.adapter.domain_genome.constraints, "evaluation_recipe": self.adapter.domain_genome.evaluation_recipe, "mutation_priors": self.adapter.domain_genome.mutation_priors})

        collapse_state = {
            "collapsed": pressures["repair_pressure"] >= 0.75,
            "drop": pressures["diversity_pressure"],
        }
        quota = allocate_quota(pressures, base_budget=self.total_budget)
        if pressures["repair_pressure"] >= 0.80:
            quota = self.quota_downshift(quota, tick=tick)
        log_event("quota_allocated", {"tick": tick, "quota": quota}, data_dir=str(self.adapter.data_dir))
        self._archive_append("quota_decisions", {"tick": tick, **quota})

        archive = archive_pressure_hook(replay_state)
        log_event("archive_pressure", {"tick": tick, **archive}, data_dir=str(self.adapter.data_dir))
        self._archive_append("pressure_snapshots", {"tick": tick, **pressures})
        mutation_payload = mutation(policy, pressures)
        log_event("mutation_selected", {"tick": tick, **mutation_payload}, data_dir=str(self.adapter.data_dir))

        execution_parent_ids = [quest_artifact.artifact_id, policy_artifact.artifact_id, *parent_ids]

        def _attempt() -> dict[str, Any]:
            return self.adapter.execute_cycle(
                tick=tick,
                quest=quest,
                policy=policy,
                quota=quota,
                parent_ids=execution_parent_ids,
                safe_mode=False,
            )

        try:
            report = self.retry_once(_attempt, tick=tick)
        except Exception as exc:
            self.checkpoint_restore()
            safe = self.safe_mode(tick=tick, reason=str(exc), parent_ids=execution_parent_ids)
            self._archive_append("repairs", {"tick": tick, "reason": str(exc), "mode": "safe_mode"})
            report = self.adapter.execute_cycle(
                tick=tick,
                quest={**quest, "quest_type": "meta"},
                policy={**policy, "safe_mode_bias": True},
                quota=safe["quota"],
                parent_ids=[safe["repair_artifact_id"], *execution_parent_ids],
                safe_mode=True,
            )

        report["supervisor_mode"] = self.mode
        report["checkpoint_best_score"] = checkpoint.get("best_score", 0.0)
        self._archive_append("artifacts", {"tick": tick, "artifact_ids": report.get("artifact_ids", []), "best_score": report.get("best_score", 0.0)})
        log_event(
            "cycle_completed",
            {
                "tick": tick,
                "signal": signal_payload,
                "best_score": report.get("best_score", 0.0),
                "artifact_ids": report.get("artifact_ids", []),
                "quest_type": quest.get("quest_type"),
                "supervisor_mode": self.mode,
            },
            data_dir=str(self.adapter.data_dir),
        )
        return report
