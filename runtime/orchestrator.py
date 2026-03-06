"""METAOS runtime orchestrator.

Grafts an Exploration Civilization MVP onto the existing loop:
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from random import Random
from typing import Any, Dict, MutableMapping, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.artifact import ArtifactStore
from core.loop import DEFAULT_STAGE_ORDER, LoopConfig, RuntimeLoop
from core.metrics import MetricsEngine
from core.mutation import mutate
from core.policy import PolicyRuntime
from core.replay import archive_pressure, rebuild_runtime_state
from core.strategy_genome import DomainGenome, StrategyGenome, canonical_domain_genome
from core.log import AppendOnlyLogger
from runtime.diversity_guard import detect_collapse
from runtime.economy_controller import QuotaAllocator
from runtime.quest_manager import Quest, QuestManager, reframing_triggers


@dataclass(slots=True)
class OrchestratorConfig:
    tick_seconds: float = 0.05
    max_ticks: int = 6
    data_dir: Path = Path("data")
    artifact_store_dir: Path = Path("artifact_store")
    canonical_domain: str = "canonical_domain"

    @classmethod
    def from_env(cls) -> "OrchestratorConfig":
        tick = _env_float("METAOS_TICK_SECONDS", 0.05)
        max_ticks = _env_int("METAOS_MAX_TICKS", 6)
        return cls(
            tick_seconds=tick if tick >= 0 else 0.05,
            max_ticks=max_ticks,
            data_dir=Path(os.getenv("METAOS_DATA_DIR", "data")),
            artifact_store_dir=Path(os.getenv("METAOS_ARTIFACT_STORE", "artifact_store")),
            canonical_domain=os.getenv("METAOS_CANONICAL_DOMAIN", "canonical_domain"),
        )


class Orchestrator:
    def __init__(self, config: OrchestratorConfig | None = None) -> None:
        self.config = config or OrchestratorConfig.from_env()
        self.config.data_dir.mkdir(parents=True, exist_ok=True)
        self.config.artifact_store_dir.mkdir(parents=True, exist_ok=True)

        self.logger = AppendOnlyLogger(log_dir=self.config.data_dir)
        self.artifact_store = ArtifactStore(store_dir=self.config.artifact_store_dir, logger=self.logger, log_dir=self.config.data_dir)
        self.metrics_engine = MetricsEngine(output_path=self.config.data_dir / "metrics.jsonl")
        self.quest_manager = QuestManager(max_selected=2)
        self.policy_runtime = PolicyRuntime(self.artifact_store, self.logger)
        self.quota_allocator = QuotaAllocator()
        self.rng = Random(7)
        self.domain_genome = canonical_domain_genome()
        self.state: Dict[str, Any] = {
            "tick": 0,
            "repair_failures": 0,
            "repeated_low_diversity_cycles": 0,
            "safe_mode": False,
            "retry_once_pending": False,
            "force_diversity_bias": False,
            "genomes": {},
            "lineage_history": {},
            "checkpoint": None,
            "active_domain_genome": self.domain_genome,
        }
        self._restore_from_truth()
        self._loop = RuntimeLoop(
            handlers={
                "signal": self.signal,
                "strategy": self.strategy,
                "artifact": self.artifact,
                "metrics": self.metrics,
                "mutation": self.mutation,
                "quest": self.quest,
                "decision": self.decision,
                "log": self.log,
            },
            config=LoopConfig(tick_seconds=self.config.tick_seconds, stage_order=DEFAULT_STAGE_ORDER),
        )

    def run(self, *, max_ticks: Optional[int] = None) -> None:
        limit = self.config.max_ticks if max_ticks is None else max_ticks
        if limit <= 0:
            self._loop.run_forever()
            return
        for _ in range(limit):
            self._loop.step()
            if self.config.tick_seconds > 0:
                time.sleep(self.config.tick_seconds)

    def signal(self, ctx: MutableMapping[str, Any]) -> Dict[str, Any]:
        replay_state = rebuild_runtime_state(self.config.data_dir)
        pressure = archive_pressure(replay_state)
        diversity_history = [row.get("diversity", 0.0) for row in replay_state.metrics_history]
        score_history = [row.get("score", 0.0) for row in replay_state.metrics_history]
        collapse = detect_collapse(diversity_history, score_history)
        pressure["collapse"] = round(max(float(pressure.get("collapse", 0.0)), float(collapse.get("drop", 0.0) or 0.0)), 6)
        quotas = self.quota_allocator.allocate(pressure, self.policy_runtime.get_policy("quota_policy"))
        self.logger.log_event("pressure_snapshot", pressure)
        self.logger.log_event("quota_decision", dict(quotas))
        self.state["replay_state"] = replay_state
        self.state["pressure"] = pressure
        self.state["quotas"] = quotas
        return {
            "tick": self.state["tick"] + 1,
            "pressure": pressure,
            "quotas": quotas,
            "collapse": collapse,
            "replay_events_seen": replay_state.events_seen,
        }

    def strategy(self, ctx: MutableMapping[str, Any]) -> Dict[str, Any]:
        signal_data = _stage_result(ctx, "signal")
        selection_policy = self.policy_runtime.get_policy("selection_policy")
        mutation_policy = self.policy_runtime.get_policy("mutation_policy")
        lineage_counts = self._lineage_counts()
        dominant_lineage, dominant_share = self._dominant_lineage(lineage_counts)
        anti_collapse = dominant_share >= float(selection_policy.get("dominance_threshold", 0.68))
        selected_lineage = self._select_lineage(lineage_counts, dominant_lineage, anti_collapse)
        fork_lineage = anti_collapse or len(lineage_counts) < int(self.domain_genome.constraints.get("minimum_lineages", 2))
        target_lineage = selected_lineage
        if fork_lineage:
            target_lineage = f"{selected_lineage}-branch-{self.state['tick'] + 1}"
        mutation_op = self._select_mutation_op(mutation_policy)
        mode = "repair" if self.state["safe_mode"] else "explore"
        if anti_collapse:
            mode = "diversify"
        if self.state["retry_once_pending"]:
            mode = "retry_once"
            self.state["retry_once_pending"] = False
        return {
            "mode": mode,
            "selected_lineage": selected_lineage,
            "target_lineage": target_lineage,
            "mutation_op": mutation_op,
            "fork_lineage": fork_lineage,
            "dominant_lineage": dominant_lineage,
            "dominant_share": round(dominant_share, 6),
            "anti_collapse": anti_collapse,
            "worker_budget": signal_data.get("quotas", {}).get("worker_budget", 1),
        }

    def artifact(self, ctx: MutableMapping[str, Any]) -> Dict[str, Any]:
        strategy_data = _stage_result(ctx, "strategy")
        quotas = self.state["quotas"]
        source_lineage = strategy_data["selected_lineage"]
        target_lineage = strategy_data["target_lineage"]
        parent = self.state["genomes"].get(source_lineage)
        if parent is None:
            parent = self._seed_lineage(source_lineage)
        pool = dict(self.state["genomes"])
        child = mutate(parent, strategy_data["mutation_op"], pool=pool, rng=self.rng).with_updates(
            budget=float(quotas.get("mutation_budget", 0.2))
        )
        if target_lineage != source_lineage:
            child = child.with_updates(parent=parent.id)
        self.state["genomes"][target_lineage] = child
        self.state["lineage_history"].setdefault(target_lineage, []).append(child.id)
        payload = {
            "strategy_genome": child.to_dict(),
            "domain_genome": self.domain_genome.to_dict(),
            "mode": strategy_data["mode"],
            "tick": self.state["tick"] + 1,
            "quotas": dict(quotas),
        }
        record = self.artifact_store.create_json_artifact(
            payload,
            metadata={
                "artifact_type": "strategy_genome",
                "lineage_id": target_lineage,
                "parent_lineage": source_lineage,
                "mutation_op": strategy_data["mutation_op"],
                "domain": self.config.canonical_domain,
            },
        )
        return {
            "artifact_id": record.artifact_id,
            "lineage_id": target_lineage,
            "parent_lineage": source_lineage,
            "mutation_op": strategy_data["mutation_op"],
            "fork_lineage": strategy_data["fork_lineage"],
        }

    def metrics(self, ctx: MutableMapping[str, Any]) -> Dict[str, Any]:
        strategy_data = _stage_result(ctx, "strategy")
        artifact_data = _stage_result(ctx, "artifact")
        quotas = self.state["quotas"]
        lineage_counts = self._lineage_counts()
        _, dominant_share = self._dominant_lineage(lineage_counts)
        tick = self.state["tick"] + 1

        novelty = 0.34 + (0.18 if strategy_data.get("mode") in {"explore", "diversify"} else 0.05)
        novelty += 0.10 if artifact_data.get("fork_lineage") else 0.0
        novelty -= 0.22 * dominant_share
        novelty -= 0.18 if tick % 5 == 0 else 0.0

        diversity = max(0.05, min(0.95, 1.0 - dominant_share))
        quality = 0.56 + (0.08 if strategy_data.get("mode") == "repair" else 0.0)
        quality -= 0.16 if tick % 4 == 0 else 0.0
        efficiency = max(0.05, 0.82 - (0.08 * float(quotas.get("exploration_budget", 0.2))) - (0.04 * int(quotas.get("worker_budget", 1))))
        cost = max(0.05, 0.92 - (0.12 * int(quotas.get("worker_budget", 1))) - (0.15 * float(quotas.get("exploration_budget", 0.2))))

        metrics = self.metrics_engine.evaluate(
            {
                "quality": _clamp(quality),
                "novelty": _clamp(novelty),
                "diversity": _clamp(diversity),
                "efficiency": _clamp(efficiency),
                "cost": _clamp(cost),
                "categories": list(lineage_counts.keys()),
            }
        )
        if metrics["diversity"] <= 0.35:
            self.state["repeated_low_diversity_cycles"] += 1
        else:
            self.state["repeated_low_diversity_cycles"] = 0
        return metrics

    def mutation(self, ctx: MutableMapping[str, Any]) -> Dict[str, Any]:
        metrics_data = _stage_result(ctx, "metrics")
        evaluation_policy = self.policy_runtime.get_policy("evaluation_policy")
        repair_policy = self.policy_runtime.get_policy("repair_policy")
        quotas = self.state["quotas"]
        minimum_score = float(evaluation_policy.get("minimum_score", 0.48))
        minimum_novelty = float(evaluation_policy.get("minimum_novelty", 0.30))
        minimum_diversity = float(evaluation_policy.get("minimum_diversity", 0.28))

        accepted = (
            metrics_data.get("score", 0.0) >= minimum_score
            and metrics_data.get("novelty", 0.0) >= minimum_novelty
            and metrics_data.get("diversity", 0.0) >= minimum_diversity
        )
        repair_attempted = not accepted
        repaired = False
        if repair_attempted:
            self.logger.log_event("repair_attempt", {"metrics": metrics_data, "tick": self.state["tick"] + 1})
            repaired = bool(quotas.get("repair_budget", 0.0) >= 0.16 and metrics_data.get("quality", 0.0) >= 0.40)
            if repaired:
                self.state["repair_failures"] = 0
                accepted = True
                self.logger.log_event("repair_succeeded", {"metrics": metrics_data, "tick": self.state["tick"] + 1})
            else:
                self.state["repair_failures"] += 1
                self.logger.log_event("repair_failed", {"metrics": metrics_data, "tick": self.state["tick"] + 1})
        else:
            self.state["repair_failures"] = 0

        if accepted and metrics_data.get("score", 0.0) >= 0.60:
            artifact_data = _stage_result(ctx, "artifact")
            self.state["checkpoint"] = {
                "artifact_id": artifact_data.get("artifact_id"),
                "lineage_id": artifact_data.get("lineage_id"),
                "metrics": dict(metrics_data),
            }
        retry_limit = int(repair_policy.get("retry_limit", 1))
        allow_retry = repair_attempted and self.state["repair_failures"] <= retry_limit
        return {
            "accepted": accepted,
            "repair_attempted": repair_attempted,
            "repair_failures": self.state["repair_failures"],
            "repaired": repaired,
            "allow_retry": allow_retry,
        }

    def quest(self, ctx: MutableMapping[str, Any]) -> Dict[str, Any]:
        metrics_data = _stage_result(ctx, "metrics")
        mutation_data = _stage_result(ctx, "mutation")
        pressure = self.state["pressure"]
        quest_policy = self.policy_runtime.get_policy("quest_policy")
        threshold = float(quest_policy.get("metric_threshold", 0.55))

        created: list[Quest] = []
        for quest in self.quest_manager.generate_from_metrics(metrics_data, threshold=threshold):
            self._log_quest("quest_proposed", quest=quest)
            created.append(quest)

        replay_state = self.state["replay_state"]
        score_history = [row.get("score", 0.0) for row in replay_state.metrics_history] + [metrics_data.get("score", 0.0)]
        novelty_history = [row.get("novelty", 0.0) for row in replay_state.metrics_history] + [metrics_data.get("novelty", 0.0)]
        diversity_history = [row.get("diversity", 0.0) for row in replay_state.metrics_history] + [metrics_data.get("diversity", 0.0)]
        lineage_share = float(pressure.get("lineage_concentration", 0.0))
        reasons = reframing_triggers(
            novelty_history=novelty_history,
            diversity_history=diversity_history,
            score_history=score_history,
            repair_failures=self.state["repair_failures"],
            lineage_share=lineage_share,
            repeated_low_diversity_cycles=self.state["repeated_low_diversity_cycles"],
        )
        if reasons and not self.quest_manager.has_active_reframing_quest():
            reframing = self.quest_manager.generate_reframing_quest(
                reasons=reasons,
                metrics=metrics_data,
                pressure=pressure,
                lineage_share=lineage_share,
            )
            self._log_quest("quest_proposed", quest=reframing)
            created.append(reframing)

        active = self.quest_manager.select_next() if not self.quest_manager.list("selected") else self.quest_manager.list("selected")[0]
        if active and active.state == "selected" and mutation_data.get("accepted"):
            if metrics_data.get("score", 0.0) >= 0.62:
                retired = self.quest_manager.retire(active.quest_id, reason="progress")
                self._log_quest("quest_retired", quest=retired, reason="progress")
                active = self.quest_manager.select_next()
        if active and active.state == "proposed":
            active = self.quest_manager.select(active.quest_id)
        if active:
            self._log_quest("quest_selected", quest=active)
        return {
            "created": [quest.quest_id for quest in created],
            "selected": active.quest_id if active else None,
            "reasons": reasons,
        }

    def decision(self, ctx: MutableMapping[str, Any]) -> Dict[str, Any]:
        signal_data = _stage_result(ctx, "signal")
        strategy_data = _stage_result(ctx, "strategy")
        mutation_data = _stage_result(ctx, "mutation")
        quest_data = _stage_result(ctx, "quest")
        repair_policy = self.policy_runtime.get_policy("repair_policy")
        selection_policy = self.policy_runtime.get_policy("selection_policy")
        pressure = signal_data.get("pressure", {})
        actions: list[str] = []

        if mutation_data.get("allow_retry") and not self.state["retry_once_pending"]:
            self.state["retry_once_pending"] = True
            actions.append("retry_once")
            self._supervisor_action("retry_once", {"lineage_id": strategy_data.get("target_lineage")})

        if self.state["repair_failures"] >= int(repair_policy.get("safe_mode_after", 3)) or ctx.get("errors"):
            self.state["safe_mode"] = True
            actions.append("safe_mode")
            self._supervisor_action("safe_mode", {"repair_failures": self.state["repair_failures"]})

        if self.state["safe_mode"]:
            self.state["quotas"] = {
                **self.state["quotas"],
                "worker_budget": 1,
                "exploration_budget": round(float(self.state["quotas"].get("exploration_budget", 0.0)) * 0.5, 6),
            }
            actions.append("quota_downshift")
            self._supervisor_action("quota_downshift", self.state["quotas"])
            checkpoint = self.state.get("checkpoint")
            if checkpoint:
                actions.append("checkpoint_restore")
                self._supervisor_action("checkpoint_restore", checkpoint)

        if float(pressure.get("lineage_concentration", 0.0)) >= float(selection_policy.get("dominance_threshold", 0.68)):
            self.state["force_diversity_bias"] = True
            actions.append("anti_collapse_guard")
            self._supervisor_action(
                "anti_collapse_guard",
                {
                    "lineage_concentration": pressure.get("lineage_concentration", 0.0),
                    "selected_lineage": strategy_data.get("target_lineage"),
                },
            )
            if quest_data.get("reasons") and not self.quest_manager.has_active_reframing_quest():
                reframing = self.quest_manager.generate_reframing_quest(
                    reasons=quest_data["reasons"],
                    metrics=_stage_result(ctx, "metrics"),
                    pressure=pressure,
                    lineage_share=float(pressure.get("lineage_concentration", 0.0)),
                    source="supervisor",
                )
                self._log_quest("quest_proposed", quest=reframing)
                actions.append("reframing_quest_injection")
                self._supervisor_action("reframing_quest_injection", {"quest_id": reframing.quest_id})

        if not actions:
            actions.append("continue")
        return {"actions": actions, "safe_mode": self.state["safe_mode"]}

    def log(self, ctx: MutableMapping[str, Any]) -> Dict[str, Any]:
        tick = self.state["tick"] + 1
        payload = {
            "tick": tick,
            "pressure": _stage_result(ctx, "signal").get("pressure", {}),
            "quotas": dict(self.state.get("quotas", {})),
            "artifact": _stage_result(ctx, "artifact"),
            "metrics": _stage_result(ctx, "metrics"),
            "quest": _stage_result(ctx, "quest"),
            "decision": _stage_result(ctx, "decision"),
            "policies": self.policy_runtime.current_policy_ids(),
            "lineages": self._lineage_counts(),
            "errors": ctx.get("errors", []),
        }
        self.logger.log_event("tick_completed", payload)
        print(json.dumps(payload, separators=(",", ":"), ensure_ascii=True), flush=True)
        self.state["tick"] = tick
        return {"logged": True}

    def _restore_from_truth(self) -> None:
        replay_state = rebuild_runtime_state(self.config.data_dir)
        self.state["replay_state"] = replay_state
        self.policy_runtime.restore_current(replay_state.current_policies)
        self.quest_manager.import_quests(replay_state.quests.values())
        self._restore_domain_genome(replay_state)
        restored = 0
        for artifact_id, payload in replay_state.artifacts.items():
            metadata = payload.get("metadata")
            if not isinstance(metadata, dict) or metadata.get("artifact_type") != "strategy_genome":
                continue
            try:
                raw = self.artifact_store.read_json_artifact(artifact_id)
                genome_data = raw.get("strategy_genome", {})
                if not isinstance(genome_data, dict):
                    continue
                genome = StrategyGenome.create(
                    id=str(genome_data.get("id")) if genome_data.get("id") else None,
                    domain=str(genome_data.get("domain", self.config.canonical_domain)),
                    eval_axes=dict(genome_data.get("eval_axes", {})),
                    mutation_ops=list(genome_data.get("mutation_ops", ["perturb", "swap", "recombine"])),
                    budget=float(genome_data.get("budget", 0.0)),
                    parent=genome_data.get("parent"),
                )
            except Exception:
                continue
            lineage_id = str(metadata.get("lineage_id") or f"lineage-{restored}")
            self.state["genomes"][lineage_id] = genome
            self.state["lineage_history"].setdefault(lineage_id, []).append(genome.id)
            restored += 1
        if restored == 0:
            self._seed_lineage("lineage-0")
            self._seed_lineage("lineage-1")

    def _restore_domain_genome(self, replay_state: Any) -> None:
        if replay_state.domain_genomes:
            latest = list(replay_state.domain_genomes.values())[-1]
            self.domain_genome = DomainGenome.create(
                adapter=str(latest.get("adapter", self.config.canonical_domain)),
                constraints=dict(latest.get("constraints", {})),
                evaluation_recipe=dict(latest.get("evaluation_recipe", {})),
                mutation_priors=dict(latest.get("mutation_priors", {})),
            )
            self.state["active_domain_genome"] = self.domain_genome
            return
        self.logger.log_event("domain_genome_loaded", self.domain_genome.to_dict())
        self.artifact_store.create_json_artifact(
            self.domain_genome.to_dict(),
            metadata={"artifact_type": "domain_genome", "lineage_id": "domain"},
        )

    def _seed_lineage(self, lineage_id: str) -> StrategyGenome:
        genome = StrategyGenome.create(
            domain=self.config.canonical_domain,
            eval_axes={"quality": 0.30, "novelty": 0.22, "diversity": 0.23, "efficiency": 0.15, "cost": 0.10},
            mutation_ops=list(self.domain_genome.mutation_priors.keys()) or ["perturb", "swap", "recombine"],
            budget=0.2,
        )
        self.state["genomes"][lineage_id] = genome
        self.state["lineage_history"].setdefault(lineage_id, []).append(genome.id)
        self.artifact_store.create_json_artifact(
            {"strategy_genome": genome.to_dict(), "domain_genome": self.domain_genome.to_dict(), "seed": True},
            metadata={
                "artifact_type": "strategy_genome",
                "lineage_id": lineage_id,
                "parent_lineage": lineage_id,
                "mutation_op": "seed",
                "domain": self.config.canonical_domain,
            },
        )
        return genome

    def _lineage_counts(self) -> Dict[str, int]:
        replay_state = self.state.get("replay_state")
        counts: Dict[str, int] = {}
        if replay_state is not None:
            counts.update(getattr(replay_state, "lineages", {}))
        for lineage_id, history in self.state.get("lineage_history", {}).items():
            counts[lineage_id] = max(counts.get(lineage_id, 0), len(history))
        return counts or {"lineage-0": 1}

    def _dominant_lineage(self, counts: Dict[str, int]) -> tuple[str, float]:
        total = sum(counts.values()) or 1
        dominant_lineage = max(counts, key=counts.get)
        return dominant_lineage, counts[dominant_lineage] / total

    def _select_lineage(self, counts: Dict[str, int], dominant_lineage: str, anti_collapse: bool) -> str:
        if anti_collapse or self.state.get("force_diversity_bias"):
            minority = sorted(counts.items(), key=lambda item: (item[1], item[0]))[0][0]
            self.state["force_diversity_bias"] = False
            return minority
        return dominant_lineage if self.rng.random() < 0.4 else sorted(counts.items(), key=lambda item: (item[1], item[0]))[0][0]

    def _select_mutation_op(self, mutation_policy: Dict[str, Any]) -> str:
        preferred = list(mutation_policy.get("preferred_ops", ["perturb", "swap", "recombine"]))
        if not preferred:
            preferred = ["perturb"]
        weighted: list[tuple[str, float]] = []
        for op in preferred:
            weighted.append((op, float(self.domain_genome.mutation_priors.get(op, 0.1))))
        weighted.sort(key=lambda item: (-item[1], item[0]))
        if self.state.get("safe_mode"):
            return "swap" if "swap" in preferred else weighted[0][0]
        return weighted[0][0] if self.rng.random() < 0.7 else weighted[-1][0]

    def _log_quest(self, event_type: str, *, quest: Quest, reason: str | None = None) -> None:
        payload: Dict[str, Any] = {"quest_id": quest.quest_id, "quest": quest.to_dict()}
        if reason:
            payload["reason"] = reason
        self.logger.log_event(event_type, payload)

    def _supervisor_action(self, hook: str, payload: Dict[str, Any]) -> None:
        self.logger.log_event("supervisor_action", {"hook": hook, **payload})


def _stage_result(ctx: MutableMapping[str, Any], stage: str) -> Dict[str, Any]:
    stage_results = ctx.get("stage_results", {})
    value = stage_results.get(stage)
    return value if isinstance(value, dict) else {}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def run() -> None:
    Orchestrator().run()


if __name__ == "__main__":
    run()
