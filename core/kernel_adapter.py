from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Iterable, Mapping

from core.artifact import create_artifact
from core.constitution_guard import validate_constitution
from core.event_log import append_event, append_jsonl, ensure_spine
from core.metrics import MetricsEngine
from domains.domain_genome import available_domain_genomes, canonical_domain_genome


DEFAULT_RUNTIME_ROOT = Path(".metaos_runtime")


class KernelAdapter:
    """Thin adapter around the artifact-first exploration runtime."""

    def __init__(
        self,
        *,
        data_dir: str | Path = DEFAULT_RUNTIME_ROOT / "data",
        artifact_dir: str | Path = DEFAULT_RUNTIME_ROOT / "artifact_store",
        state_dir: str | Path = DEFAULT_RUNTIME_ROOT / "state",
        archive_dir: str | Path = DEFAULT_RUNTIME_ROOT / "archive",
        domain_name: str = "code_domain",
    ) -> None:
        self.data_dir = Path(data_dir)
        self.artifact_dir = Path(artifact_dir)
        self.state_dir = Path(state_dir)
        self.archive_dir = Path(archive_dir)
        self.domain_name = domain_name
        self.metrics_engine = MetricsEngine(output_path=self.data_dir / "metrics.jsonl")
        self.domain_genome = canonical_domain_genome(domain_name)
        self.domain_genomes = available_domain_genomes()
        self.checkpoint_path = self.state_dir / "checkpoint.json"
        self.quest_state_path = self.state_dir / "quest.json"

    def validate(self) -> dict[str, Any]:
        constitution = validate_constitution()
        spine = ensure_spine(self.data_dir)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        return {
            "ok": True,
            "domain": self.domain_name,
            "data_dir": str(spine.root),
            "artifact_dir": str(self.artifact_dir),
            "state_dir": str(self.state_dir),
            "archive_dir": str(self.archive_dir),
            "checkpoint_available": self.checkpoint_path.exists(),
            "constitution": constitution,
            "domains": sorted(self.domain_genomes),
        }

    def checkpoint_restore(self) -> dict[str, Any]:
        if not self.checkpoint_path.exists():
            return {"population": [], "best_score": 0.0, "tick": 0, "best_artifact_id": ""}
        with self.checkpoint_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return payload if isinstance(payload, dict) else {"population": [], "best_score": 0.0, "tick": 0, "best_artifact_id": ""}

    def save_checkpoint(self, population: list[dict[str, Any]], best_score: float, tick: int, *, best_artifact_id: str = "") -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        payload = {"population": population, "best_score": best_score, "tick": tick, "best_artifact_id": best_artifact_id}
        tmp_path = self.checkpoint_path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=True, indent=2)
        tmp_path.replace(self.checkpoint_path)

    def _seed_strategy(self, domain: str, population: list[dict[str, Any]], transfer_strategy: Mapping[str, Any] | None = None) -> dict[str, float]:
        genome = self.domain_genomes.get(domain, self.domain_genome)
        if transfer_strategy:
            return genome.transfer(transfer_strategy, pressure=0.25)
        if population:
            base = random.choice(population)
            if isinstance(base, dict):
                return genome.normalize(base)
        return dict(genome.seed_strategy)

    def _candidate_metrics(self, strategy: Mapping[str, float], *, domain: str, tick: int, worker_index: int, safe_mode: bool) -> dict[str, float]:
        genome = self.domain_genomes.get(domain, self.domain_genome)
        score = genome.evaluate(strategy)
        usefulness = max(0.0, min(1.0, (strategy.get("quality", 0.0) * 0.5) + (strategy.get("usefulness", 0.0) * 0.5)))
        persistence = max(0.0, min(1.0, (strategy.get("persistence", 0.0) * 0.6) + (strategy.get("efficiency", 0.0) * 0.4)))
        recombination = max(0.0, min(1.0, strategy.get("recombination", 0.0)))
        metrics = self.metrics_engine.evaluate(
            {
                "quality": strategy.get("quality", 0.0),
                "novelty": strategy.get("novelty", 0.0),
                "diversity": strategy.get("diversity", 0.0),
                "efficiency": strategy.get("efficiency", 0.0),
                "cost": strategy.get("cost", 0.0),
                "score": score,
                "tick": tick,
                "throughput": 1.0 if not safe_mode else 0.5,
                "latency_ms": 60.0 + (worker_index * 10.0),
                "latency_target_ms": 200.0,
            }
        )
        metrics.update(
            {
                "score": round(score, 6),
                "usefulness": round(usefulness, 6),
                "persistence": round(persistence, 6),
                "recombination": round(recombination, 6),
                "tick": float(tick),
            }
        )
        append_jsonl(
            self.archive_dir / "artifacts.jsonl",
            {"tick": tick, "domain": domain, "score": score, "strategy": dict(strategy), "metrics": dict(metrics)},
        )
        return metrics

    def execute_cycle(
        self,
        *,
        tick: int,
        quests: list[Mapping[str, Any]] | Mapping[str, Any],
        policy: Mapping[str, Any],
        quota: Mapping[str, float],
        parent_ids: list[str],
        safe_mode: bool = False,
        transfer_strategy: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        checkpoint = self.checkpoint_restore()
        population = list(checkpoint.get("population", [])) if isinstance(checkpoint.get("population", []), list) else []
        quest_list = [dict(quests)] if isinstance(quests, Mapping) else [dict(item) for item in quests]
        domains = [str(item.get("domain") or item.get("domain_hint") or self.domain_name) for item in quest_list]
        if self.domain_name not in domains:
            domains.insert(0, self.domain_name)
        candidate_count = 1 if safe_mode else max(2, int(quota.get("worker_budget", 2)))
        rows: list[dict[str, Any]] = []
        best_artifact_id = ""
        best_score = float(checkpoint.get("best_score", 0.0) or 0.0)

        for worker_index in range(candidate_count):
            domain = domains[worker_index % len(domains)]
            genome = self.domain_genomes.get(domain, self.domain_genome)
            base_strategy = self._seed_strategy(domain, population, transfer_strategy if worker_index == 0 else None)
            drift = float(policy.get("mutation_scale", 0.08)) * (0.5 if safe_mode else 1.0)
            strategy = base_strategy if safe_mode else genome.mutate(base_strategy, drift=drift)
            metrics = self._candidate_metrics(strategy, domain=domain, tick=tick, worker_index=worker_index, safe_mode=safe_mode)
            quest = quest_list[worker_index % len(quest_list)]
            lineage_id = str(parent_ids[worker_index % len(parent_ids)]) if parent_ids else f"{domain}:{tick}:{worker_index}"
            strategy_artifact = create_artifact(
                "strategy",
                {"strategy": strategy, "policy": dict(policy), "quota": dict(quota), "domain": domain, "quest": quest},
                parent_ids=parent_ids,
                domain=domain,
                quest_id=str(quest.get("id") or quest.get("quest_id") or ""),
                source="kernel_adapter",
                score=float(metrics["score"]),
                tick=tick,
                artifact_dir=self.artifact_dir,
                data_dir=self.data_dir,
                metadata={"lineage_id": lineage_id},
            )
            evaluation_artifact = create_artifact(
                "evaluation",
                {"metrics": metrics, "strategy_artifact_id": strategy_artifact.artifact_id, "domain": domain},
                parent_ids=[strategy_artifact.artifact_id, *parent_ids],
                domain=domain,
                quest_id=str(quest.get("id") or quest.get("quest_id") or ""),
                source="kernel_adapter",
                score=float(metrics["score"]),
                tick=tick,
                artifact_dir=self.artifact_dir,
                data_dir=self.data_dir,
                metadata={"lineage_id": lineage_id},
            )
            discovery_artifact = create_artifact(
                "discovery",
                {"domain": domain, "strategy": strategy, "metrics": metrics, "transfer_seed": dict(transfer_strategy or {})},
                parent_ids=[evaluation_artifact.artifact_id],
                domain=domain,
                quest_id=str(quest.get("id") or quest.get("quest_id") or ""),
                source="kernel_adapter",
                score=float(metrics["score"]),
                tick=tick,
                artifact_dir=self.artifact_dir,
                data_dir=self.data_dir,
                metadata={"lineage_id": lineage_id},
            )
            rows.append(
                {
                    "domain": domain,
                    "strategy": strategy,
                    "metrics": metrics,
                    "artifact_ids": [strategy_artifact.artifact_id, evaluation_artifact.artifact_id, discovery_artifact.artifact_id],
                    "score": float(metrics["score"]),
                }
            )
            if float(metrics["score"]) >= best_score:
                best_score = float(metrics["score"])
                best_artifact_id = discovery_artifact.artifact_id

        sorted_rows = sorted(rows, key=lambda row: row["score"], reverse=True)
        next_population = [row["strategy"] for row in sorted_rows[: min(8, len(sorted_rows))]]
        self.save_checkpoint(next_population, best_score, tick, best_artifact_id=best_artifact_id)
        append_event(
            "cycle_completed",
            {
                "tick": tick,
                "best_score": best_score,
                "best_artifact_id": best_artifact_id,
                "population_size": len(next_population),
                "domains": [row["domain"] for row in rows],
            },
            data_dir=self.data_dir,
        )
        return {
            "tick": tick,
            "best_score": best_score,
            "best_artifact_id": best_artifact_id,
            "population": next_population,
            "population_size": len(next_population),
            "candidate_rows": rows,
            "metrics": dict(sorted_rows[0]["metrics"] if sorted_rows else {}),
            "artifact_ids": [artifact_id for row in rows for artifact_id in row["artifact_ids"]],
        }
