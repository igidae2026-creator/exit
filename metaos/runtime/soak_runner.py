from __future__ import annotations

import collections
import contextlib
import json
import os
import random
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence
from unittest.mock import patch

import metaos.policy.evaluation_artifact as evaluation_artifact
import metaos.registry.artifact_registry as artifact_registry
import metaos.runtime.artifact_civilization as artifact_civilization
import metaos.runtime.exploration_strategy_artifact as exploration_strategy_artifact
import metaos.runtime.oed_orchestrator as oed_orchestrator
from metaos.archive.archive import save
from metaos.archive.civilization_memory import remember
from metaos.core.supervisor import guarded_step
from metaos.runtime.collapse_guard import detect_guard_state
from metaos.runtime.oed_orchestrator import step as oed_step


class SoakResult:
    def __init__(self, ticks: list[dict[str, Any]], summary: dict[str, Any]) -> None:
        self.ticks = ticks
        self.summary = summary

    def __iter__(self) -> Iterator[Any]:
        return iter((self.ticks, self.summary))

    def __len__(self) -> int:
        return len(self.ticks)

    def __getitem__(self, item: Any) -> Any:
        return self.ticks[item]

    def __bool__(self) -> bool:
        return bool(self.ticks)


def _metrics_path() -> Path:
    path = Path(os.environ.get("METAOS_METRICS", ".metaos_runtime/data/metrics.jsonl"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _metrics_row(tick: int, metrics: Mapping[str, float], state: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "tick": tick,
        **dict(metrics),
        "workers": state.get("workers", 0),
        "quest": state.get("quest", {}),
        "pressure": state.get("pressure", {}),
        "stabilized_pressure": state.get("stabilized_pressure", state.get("pressure", {})),
        "market": state.get("market", {}),
        "stabilized_market": state.get("stabilized_market", state.get("market", {})),
        "budgets": state.get("budgets", {}),
        "routing": state.get("routing", {}),
        "guard": state.get("guard", {}),
        "repair": state.get("repair"),
    }


def append_metrics_snapshot(tick: int, metrics: Mapping[str, float], state: Mapping[str, Any]) -> None:
    row = _metrics_row(tick, metrics, state)
    with _metrics_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def _is_soak_fast_mode() -> bool:
    return os.environ.get("METAOS_SOAK_FAST") == "1"


class _BufferedJsonlWriter:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.buffer: list[str] = []

    def append(self, row: Mapping[str, Any]) -> None:
        self.buffer.append(json.dumps(dict(row), ensure_ascii=True) + "\n")

    def flush(self) -> None:
        if not self.buffer:
            return
        with self.path.open("a", encoding="utf-8") as handle:
            handle.writelines(self.buffer)
        self.buffer.clear()


class _FastSoakRuntime:
    def __init__(self, flush_every: int = 10) -> None:
        self.flush_every = max(1, int(flush_every))
        self.metrics_writer = _BufferedJsonlWriter(_metrics_path())
        self.archive_writer = _BufferedJsonlWriter(Path(os.environ.get("METAOS_ARCHIVE", ".metaos_runtime/archive/archive.jsonl")))
        self.memory_writer = _BufferedJsonlWriter(
            Path(os.environ.get("METAOS_CIVILIZATION_MEMORY", ".metaos_runtime/archive/civilization_memory.jsonl"))
        )
        self.metric_history: collections.deque[dict[str, Any]] = collections.deque(maxlen=64)
        self.guard_history: collections.deque[dict[str, Any]] = collections.deque(maxlen=64)
        self.cooldown_history: collections.deque[dict[str, Any]] = collections.deque(maxlen=64)
        self.routing_history: collections.deque[dict[str, Any]] = collections.deque(maxlen=64)
        self.evaluation_rows: list[dict[str, Any]] = []
        self.strategy_rows: list[dict[str, Any]] = []
        self.parent_counts: collections.Counter[str] = collections.Counter()
        self.total_edges = 0
        self._patches: contextlib.ExitStack | None = None

    def __enter__(self) -> _FastSoakRuntime:
        stack = contextlib.ExitStack()
        stack.enter_context(patch.object(oed_orchestrator, "metrics_tail", self.metrics_tail))
        stack.enter_context(patch.object(oed_orchestrator, "plateau", self.plateau))
        stack.enter_context(patch.object(oed_orchestrator, "novelty_drop", self.novelty_drop))
        stack.enter_context(patch.object(oed_orchestrator, "concentration", self.concentration))
        stack.enter_context(patch.object(oed_orchestrator, "load_evaluations", self.load_evaluations))
        stack.enter_context(patch.object(oed_orchestrator, "load_exploration_strategies", self.load_exploration_strategies))
        stack.enter_context(patch.object(artifact_civilization, "_register_artifact", self.register_artifact))
        stack.enter_context(patch.object(artifact_civilization, "_register_evaluation", self.register_evaluation))
        stack.enter_context(patch.object(artifact_civilization, "_register_exploration_strategy", self.register_exploration_strategy))
        stack.enter_context(patch.object(oed_orchestrator, "save", self.save))
        stack.enter_context(patch.object(oed_orchestrator, "remember", self.remember))
        stack.enter_context(patch(__name__ + ".save", self.save))
        stack.enter_context(patch(__name__ + ".remember", self.remember))
        self._patches = stack
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        try:
            self.flush()
        finally:
            if self._patches is not None:
                self._patches.close()
                self._patches = None

    def _metric_values(self, window: int, key: str) -> list[float]:
        rows = list(self.metric_history)[-window:]
        return [float(row.get(key, 0.0)) for row in rows if isinstance(row, Mapping)]

    def metrics_tail(self, n: int = 200) -> list[dict[str, Any]]:
        return list(self.metric_history)[-n:]

    def plateau(self, window: int = 50, eps: float = 0.02) -> bool:
        vals = self._metric_values(window, "score")
        if len(vals) < max(10, window // 2):
            return False
        return (max(vals) - min(vals)) <= eps

    def novelty_drop(self, window: int = 50, threshold: float = 0.35) -> bool:
        vals = self._metric_values(window, "novelty")
        if not vals:
            return False
        return (sum(vals) / len(vals)) < threshold

    def concentration(self) -> float:
        if self.total_edges <= 0:
            return 0.0
        top = max(self.parent_counts.values(), default=0)
        return top / self.total_edges if self.total_edges else 0.0

    def load_evaluations(self) -> list[dict[str, Any]]:
        return list(self.evaluation_rows)

    def load_exploration_strategies(self) -> list[dict[str, Any]]:
        return list(self.strategy_rows)

    def register_artifact(self, data: Any, parent: str | None = None, **kwargs: Any) -> str:
        artifact_id = artifact_registry.register(data, parent=parent, **kwargs)
        if parent:
            self.parent_counts[str(parent)] += 1
            self.total_edges += 1
        return artifact_id

    def register_evaluation(self, evaluation: Mapping[str, Any], pressure: Mapping[str, float], score: float, *, parent: str | None = None) -> str:
        artifact_id = evaluation_artifact.register_evaluation(evaluation, pressure, score, parent=parent)
        self.evaluation_rows.append(
            {
                "id": artifact_id,
                "parent": parent,
                "evaluation": dict(evaluation),
                "pressure": dict(pressure),
                "score": float(score),
            }
        )
        return artifact_id

    def register_exploration_strategy(
        self,
        strategy: Mapping[str, Any],
        pressure: Mapping[str, float],
        market: Mapping[str, float],
        score: float,
        *,
        parent: str | None = None,
    ) -> str:
        artifact_id = exploration_strategy_artifact.register_strategy(strategy, pressure, market, score, parent=parent)
        self.strategy_rows.append(
            {
                "id": artifact_id,
                "parent": parent,
                "strategy": dict(strategy),
                "pressure": dict(pressure),
                "market": dict(market),
                "score": float(score),
            }
        )
        return artifact_id

    def save(self, kind: str, payload: Any) -> None:
        self.archive_writer.append({"kind": kind, "payload": payload})

    def remember(self, kind: str, payload: Any) -> None:
        self.memory_writer.append({"kind": kind, "payload": payload})

    def append_metrics_snapshot(self, tick: int, metrics: Mapping[str, float], state: Mapping[str, Any]) -> None:
        row = _metrics_row(tick, metrics, state)
        self.metric_history.append(row)
        self.metrics_writer.append(row)

    def record_histories(self, metrics: Mapping[str, float], state: Mapping[str, Any]) -> None:
        row = {**dict(metrics), **dict(state)}
        self.guard_history.append(row)
        self.cooldown_history.append(
            {
                "tick": state.get("tick"),
                "quest": state.get("quest", {}),
                "repair": state.get("repair"),
                "guard": state.get("guard", {}),
                "cooldown": state.get("cooldown", {}),
            }
        )
        self.routing_history.append(
            {
                "tick": state.get("tick"),
                "domain": state.get("domain"),
                "routing": state.get("routing", {}),
                "guard": state.get("guard", {}),
            }
        )

    def maybe_flush(self, tick: int, total_ticks: int) -> None:
        if tick % self.flush_every == 0 or tick == total_ticks:
            self.flush()

    def flush(self) -> None:
        self.metrics_writer.flush()
        self.archive_writer.flush()
        self.memory_writer.flush()


class _SummaryTracker:
    def __init__(self) -> None:
        self.max_workers = 0
        self.min_workers: int | None = None
        self.total_workers = 0
        self.count = 0
        self.repair_count = 0
        self.meta_count = 0
        self.reframing_count = 0
        self.freeze_count = 0

    def update(self, report: Mapping[str, Any]) -> None:
        workers = int(report.get("workers", 0))
        self.max_workers = max(self.max_workers, workers)
        self.min_workers = workers if self.min_workers is None else min(self.min_workers, workers)
        self.total_workers += workers
        self.count += 1
        if report.get("repair"):
            self.repair_count += 1
        quest = report.get("quest", {}) if isinstance(report.get("quest"), Mapping) else {}
        qtype = str(quest.get("type", ""))
        if qtype == "meta":
            self.meta_count += 1
        if qtype == "reframing":
            self.reframing_count += 1
        guard = report.get("guard", {}) if isinstance(report.get("guard"), Mapping) else {}
        if bool(guard.get("freeze_export")):
            self.freeze_count += 1

    def summary(self) -> dict[str, Any]:
        count = self.count or 1
        return {
            "max_workers": self.max_workers,
            "min_workers": 0 if self.min_workers is None else self.min_workers,
            "avg_workers": round(self.total_workers / count, 4),
            "repair_count": self.repair_count,
            "meta_count": self.meta_count,
            "reframing_count": self.reframing_count,
            "freeze_count": self.freeze_count,
        }


def _generated_metrics(ticks: int, seed: int | None) -> list[dict[str, float]]:
    rng = random.Random(seed)
    out: list[dict[str, float]] = []
    score = 0.58
    novelty = 0.3
    diversity = 0.34
    cost = 0.18
    fail_rate = 0.09
    for tick in range(max(0, ticks)):
        cycle = tick % 48
        stress = 0.0
        if 14 <= cycle <= 23:
            stress = 0.18
        elif 24 <= cycle <= 30:
            stress = 0.1
        recovery = 0.06 if 31 <= cycle <= 40 else 0.0

        score_target = 0.62 - (0.16 * stress) + (0.08 * recovery)
        novelty_target = 0.26 - (0.18 * stress) + (0.1 * recovery)
        diversity_target = 0.33 - (0.08 * stress) + (0.06 * recovery)
        cost_target = 0.17 + (0.28 * stress) - (0.08 * recovery)
        fail_target = 0.08 + (0.25 * stress) - (0.08 * recovery)

        score = max(0.0, min(1.0, score + 0.18 * (score_target - score) + rng.uniform(-0.025, 0.025)))
        novelty = max(0.0, min(1.0, novelty + 0.22 * (novelty_target - novelty) + rng.uniform(-0.03, 0.03)))
        diversity = max(0.0, min(1.0, diversity + 0.18 * (diversity_target - diversity) + rng.uniform(-0.025, 0.025)))
        cost = max(0.0, min(1.0, cost + 0.2 * (cost_target - cost) + rng.uniform(-0.02, 0.02)))
        fail_rate = max(0.0, min(1.0, fail_rate + 0.22 * (fail_target - fail_rate) + rng.uniform(-0.02, 0.02)))
        out.append(
            {
                "score": round(score, 4),
                "novelty": round(novelty, 4),
                "diversity": round(diversity, 4),
                "cost": round(cost, 4),
                "fail_rate": round(fail_rate, 4),
            }
        )
    return out


def run_soak(
    metrics_sequence: Sequence[Mapping[str, float]] | None = None,
    *,
    ticks: int | None = None,
    seed: int | None = None,
    fail_open: bool = True,
    initial_policy: Mapping[str, float] | None = None,
    workers: int = 4,
    domain: str = "default",
) -> SoakResult:
    sequence = list(metrics_sequence) if metrics_sequence is not None else _generated_metrics(int(ticks or 0), seed)
    worker_cap = max(8, int(workers) * 8)
    state: dict[str, Any] = {"policy": dict(initial_policy or {}), "workers": workers, "domain": domain}
    reports: list[dict[str, Any]] = []
    summary = _SummaryTracker()
    fast_runtime = _FastSoakRuntime() if _is_soak_fast_mode() else None

    with fast_runtime or contextlib.nullcontext():
        total_ticks = len(sequence)
        guard_history: collections.deque[dict[str, Any]] = collections.deque(maxlen=64 if fast_runtime is not None else total_ticks or None)
        for tick, metrics in enumerate(sequence, start=1):
            if fast_runtime is not None:
                fast_runtime.append_metrics_snapshot(tick, metrics, state)
            else:
                append_metrics_snapshot(tick, metrics, state)

            def _step(current_state: dict[str, Any]) -> dict[str, Any]:
                result = oed_step(
                    metrics=metrics,
                    policy=current_state.get("policy"),
                    workers=min(worker_cap, int(current_state.get("workers", workers))),
                    domain=str(current_state.get("domain", domain)),
                    parent=current_state.get("artifact_id"),
                )
                next_state = {
                    "tick": tick,
                    "artifact_id": result.get("artifact_id"),
                    "policy": result.get("policy", {}),
                    "workers": min(worker_cap, int(result.get("workers", workers))),
                    "domain": result.get("domain", domain),
                    "quest": result.get("quest", {}),
                    "pressure": result.get("pressure", {}),
                    "stabilized_pressure": result.get("stabilized_pressure", result.get("pressure", {})),
                    "repair": result.get("repair"),
                    "genome": result.get("genome"),
                    "market": result.get("market", {}),
                    "stabilized_market": result.get("stabilized_market", result.get("market", {})),
                    "budgets": result.get("budgets", {}),
                    "routing": result.get("routing", {}),
                    "guard": result.get("guard", {}),
                    "cooldown": result.get("cooldown", {}),
                }
                save("soak_snapshot", next_state)
                remember("soak_snapshot", next_state)
                return next_state

            if fail_open:
                state = dict(guarded_step(_step, state) or state)
            else:
                state = dict(_step(state))
            guard_history.append({**dict(metrics), **state})
            state["guard"] = detect_guard_state(guard_history)
            if fast_runtime is not None:
                fast_runtime.record_histories(metrics, state)
                fast_runtime.maybe_flush(tick, total_ticks)
            reports.append(dict(state))
            summary.update(state)
    return SoakResult(reports, summary.summary())
