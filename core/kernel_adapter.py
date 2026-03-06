from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Mapping

from core.artifact import create_artifact
from core.constitution_guard import validate_constitution
from core.autonomous_daemon import evaluate_strategy, mutate_strategy, normalize_strategy, random_strategy, resolve_domain_generate
from core.event_log import ensure_spine
from core.metrics import MetricsEngine
from core.replay_engine import replay_sample
from domains.domain_genome import canonical_domain_genome


class KernelAdapter:
    """Thin adapter around the existing runtime and early OED helpers."""

    def __init__(
        self,
        *,
        data_dir: str | Path = "data",
        artifact_dir: str | Path = "artifact_store",
        state_dir: str | Path = "state",
        archive_dir: str | Path = "archive",
        domain_name: str = "code_domain",
    ) -> None:
        self.data_dir = Path(data_dir)
        self.artifact_dir = Path(artifact_dir)
        self.state_dir = Path(state_dir)
        self.archive_dir = Path(archive_dir)
        self.domain_name = domain_name
        self.metrics_engine = MetricsEngine(output_path=self.data_dir / "metrics.jsonl")
        self.domain_genome = canonical_domain_genome()
        self.checkpoint_path = self.state_dir / "checkpoint.json"

    def validate(self) -> dict[str, Any]:
        validate_constitution()
        spine = ensure_spine(self.data_dir)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        generator = resolve_domain_generate(self.domain_name)
        if generator is None:
            raise RuntimeError(f"domain generator unavailable: {self.domain_name}")
        return {
            "ok": True,
            "domain": self.domain_name,
            "data_dir": str(spine.root),
            "artifact_dir": str(self.artifact_dir),
            "state_dir": str(self.state_dir),
            "archive_dir": str(self.archive_dir),
            "checkpoint_available": (self.state_dir / "checkpoint.json").exists(),
        }

    def checkpoint_restore(self) -> dict[str, Any]:
        if not self.checkpoint_path.exists():
            return {"population": [], "best_score": float("-inf"), "tick": 0}
        with self.checkpoint_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return {
            "population": list(payload.get("population", [])),
            "best_score": float(payload.get("best_score", float("-inf"))),
            "tick": int(payload.get("tick", 0)),
        }

    def save_checkpoint(self, population: list[dict[str, float]], best_score: float, tick: int) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        payload = {"population": population, "best_score": best_score, "tick": tick}
        tmp_path = self.checkpoint_path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=True)
        tmp_path.replace(self.checkpoint_path)

    def _seed_strategy(self) -> dict[str, float]:
        candidate = replay_sample()
        if candidate is None:
            checkpoint = self.checkpoint_restore()
            population = checkpoint.get("population", [])
            if isinstance(population, list) and population:
                candidate = random.choice(population)
        if candidate is None:
            generator = resolve_domain_generate(self.domain_name)
            if generator is not None:
                candidate = generator()
            else:
                candidate = self.domain_genome.generate()
        normalized = normalize_strategy(candidate)
        return normalized or random_strategy()

    def execute_cycle(
        self,
        *,
        tick: int,
        quest: Mapping[str, Any],
        policy: Mapping[str, Any],
        quota: Mapping[str, float],
        parent_ids: list[str],
        safe_mode: bool = False,
    ) -> dict[str, Any]:
        candidate_count = 1 if safe_mode else max(1, min(3, int(sum(float(v) for v in quota.values()) // 30) + 1))

        result_rows: list[dict[str, Any]] = []
        for _ in range(candidate_count):
            base_strategy = self._seed_strategy()
            strategy = base_strategy if safe_mode else self.domain_genome.mutate(base_strategy)
            score = float(self.domain_genome.evaluate(strategy))
            metrics = self.metrics_engine.evaluate(
                {
                    **strategy,
                    "score": score,
                    "tick": tick,
                    "throughput": 1.0 if not safe_mode else 0.5,
                    "latency_ms": 80.0 if not safe_mode else 150.0,
                    "latency_target_ms": 200.0,
                }
            )

            strategy_artifact = create_artifact(
                "strategy",
                {
                    "strategy": strategy,
                    "base_strategy": base_strategy,
                    "policy": dict(policy),
                    "quota": dict(quota),
                },
                parent_ids=parent_ids,
                domain=self.domain_name,
                quest_id=str(quest.get("id") or ""),
                source="kernel_adapter",
                score=score,
                tick=tick,
                artifact_dir=self.artifact_dir,
                data_dir=str(self.data_dir),
            )
            evaluation_artifact = create_artifact(
                "evaluation",
                {"metrics": metrics, "score": score},
                parent_ids=[strategy_artifact.artifact_id, *parent_ids],
                domain=self.domain_name,
                quest_id=str(quest.get("id") or ""),
                source="kernel_adapter",
                score=score,
                tick=tick,
                artifact_dir=self.artifact_dir,
                data_dir=str(self.data_dir),
            )
            output_artifact = create_artifact(
                "output",
                {
                    "strategy": strategy,
                    "quest_type": quest.get("quest_type"),
                    "policy_version": policy.get("policy_version"),
                    "safe_mode": safe_mode,
                },
                parent_ids=[strategy_artifact.artifact_id, evaluation_artifact.artifact_id],
                domain=self.domain_name,
                quest_id=str(quest.get("id") or ""),
                source="kernel_adapter",
                score=score,
                tick=tick,
                artifact_dir=self.artifact_dir,
                data_dir=str(self.data_dir),
            )
            result_rows.append(
                {
                    "strategy": strategy,
                    "metrics": metrics,
                    "score": score,
                    "artifact_ids": [
                        strategy_artifact.artifact_id,
                        evaluation_artifact.artifact_id,
                        output_artifact.artifact_id,
                    ],
                }
            )

        best = max(result_rows, key=lambda row: float(row["score"]))
        checkpoint = self.checkpoint_restore()
        population = checkpoint.get("population", [])
        next_population = [best["strategy"]]
        if isinstance(population, list):
            next_population.extend(population[:7])
        self.save_checkpoint(next_population, float(best["score"]), tick)
        return {
            "tick": tick,
            "best_score": float(best["score"]),
            "metrics": dict(best["metrics"]),
            "artifact_ids": list(best["artifact_ids"]),
            "population_size": len(next_population),
        }
