from __future__ import annotations

import collections
import contextlib
import json
import os
import random
import uuid
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence
from unittest.mock import patch

import metaos.policy.evaluation_artifact as evaluation_artifact
import metaos.observer.metrics_history as metrics_history
import metaos.observer.pressure_engine as pressure_engine
import metaos.registry.artifact_registry as artifact_registry
import metaos.registry.lineage_graph as lineage_graph
import metaos.runtime.artifact_civilization as artifact_civilization
import metaos.runtime.domain_pool as domain_pool
import metaos.runtime.domain_router as domain_router
import metaos.runtime.exploration_strategy_artifact as exploration_strategy_artifact
import runtime.oed_orchestrator as oed_orchestrator
import metaos.runtime.strategy_of_strategy as strategy_of_strategy_registry
from metaos.archive.archive import save
from metaos.archive.civilization_memory import remember
from metaos.core.supervisor import guarded_step
from metaos.runtime.collapse_guard import detect_guard_state
from runtime.oed_orchestrator import step as oed_step


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


def _runtime_path(env_name: str, root_relative: str, default_path: str) -> Path:
    explicit = os.environ.get(env_name)
    if explicit:
        path = Path(explicit)
    else:
        root = os.environ.get("METAOS_ROOT")
        path = Path(root) / root_relative if root else Path(default_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _metrics_path() -> Path:
    return _runtime_path("METAOS_METRICS", "metrics.jsonl", ".metaos_runtime/data/metrics.jsonl")


def _archive_path() -> Path:
    return _runtime_path("METAOS_ARCHIVE", "archive.jsonl", ".metaos_runtime/archive/archive.jsonl")


def _civilization_memory_path() -> Path:
    return _runtime_path("METAOS_CIVILIZATION_MEMORY", "archive/civilization_memory.jsonl", ".metaos_runtime/archive/civilization_memory.jsonl")


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
        "policy": state.get("policy", {}),
        "budgets": state.get("budgets", {}),
        "routing": state.get("routing", {}),
        "civilization_selection": state.get("civilization_selection", {}),
        "population": state.get("population", {}),
        "governance": state.get("governance", {}),
        "economy": state.get("economy", {}),
        "exploration_economy_state": state.get("exploration_economy_state", {}),
        "resource_allocation": state.get("resource_allocation", {}),
        "ecology": state.get("ecology", {}),
        "civilization_state": state.get("civilization_state", {}),
        "civilization_stability": state.get("civilization_stability", {}),
        "strategy_of_strategy": state.get("strategy_of_strategy", {}),
        "exploration_cycle": state.get("exploration_cycle", {}),
        "meta_exploration": state.get("meta_exploration", {}),
        "guard": state.get("guard", {}),
        "repair": state.get("repair"),
    }


def _fast_metrics_row(tick: int, metrics: Mapping[str, float], state: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "tick": tick,
        "score": metrics.get("score", 0.0),
        "novelty": metrics.get("novelty", 0.0),
        "diversity": metrics.get("diversity", 0.0),
        "cost": metrics.get("cost", 0.0),
        "fail_rate": metrics.get("fail_rate", 0.0),
        "workers": state.get("workers", 0),
        "domain": state.get("domain", "default"),
        "quest": state.get("quest", {}),
        "pressure": state.get("pressure", {}),
        "stabilized_pressure": state.get("stabilized_pressure", state.get("pressure", {})),
        "policy": state.get("policy", {}),
        "routing": state.get("routing", {}),
        "civilization_selection": state.get("civilization_selection", {}),
        "strategy_of_strategy": state.get("strategy_of_strategy", {}),
        "resource_allocation": state.get("resource_allocation", {}),
        "exploration_economy_state": state.get("exploration_economy_state", {}),
        "civilization_state": state.get("civilization_state", {}),
        "civilization_stability": state.get("civilization_stability", {}),
        "exploration_cycle": state.get("exploration_cycle", {}),
        "meta_exploration": state.get("meta_exploration", {}),
        "guard": state.get("guard", {}),
        "repair": state.get("repair"),
    }


def _fast_guard_row(metrics: Mapping[str, float], state: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "score": metrics.get("score", 0.0),
        "novelty": metrics.get("novelty", 0.0),
        "diversity": metrics.get("diversity", 0.0),
        "cost": metrics.get("cost", 0.0),
        "fail_rate": metrics.get("fail_rate", 0.0),
        "domain": state.get("domain", "default"),
        "quest": state.get("quest", {}),
        "pressure": state.get("pressure", {}),
        "routing": state.get("routing", {}),
        "repair": state.get("repair"),
        "guard": state.get("guard", {}),
        "cooldown": state.get("cooldown", {}),
        "meta_exploration": state.get("meta_exploration", {}),
        "exploration_cycle": state.get("exploration_cycle", {}),
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
        self.buffer: list[dict[str, Any]] = []

    def append(self, row: Mapping[str, Any]) -> None:
        self.buffer.append(dict(row))

    def flush(self) -> None:
        if not self.buffer:
            return
        with self.path.open("a", encoding="utf-8") as handle:
            handle.writelines(json.dumps(row, ensure_ascii=True) + "\n" for row in self.buffer)
        self.buffer.clear()


class _FastSoakRuntime:
    def __init__(self, flush_every: int = 10) -> None:
        self.flush_every = max(1, int(flush_every))
        self.metrics_writer = _BufferedJsonlWriter(_metrics_path())
        self.archive_writer = _BufferedJsonlWriter(_archive_path())
        self.memory_writer = _BufferedJsonlWriter(_civilization_memory_path())
        self.metric_history: collections.deque[dict[str, Any]] = collections.deque(maxlen=64)
        self.guard_history: collections.deque[dict[str, Any]] = collections.deque(maxlen=64)
        self.cooldown_history: collections.deque[dict[str, Any]] = collections.deque(maxlen=64)
        self.routing_history: collections.deque[dict[str, Any]] = collections.deque(maxlen=64)
        self.ecology_history: collections.deque[dict[str, Any]] = collections.deque(maxlen=64)
        self.evaluation_rows: list[dict[str, Any]] = []
        self.strategy_rows: list[dict[str, Any]] = []
        self.strategy_of_strategy_rows: list[dict[str, Any]] = []
        self.parent_counts: collections.Counter[str] = collections.Counter()
        self.population_counts: collections.Counter[str] = collections.Counter()
        self.latest_ecology: dict[str, Any] = {}
        self.latest_civilization_selection: dict[str, Any] = {}
        self.total_edges = 0
        self.domain_pool: dict[str, dict[str, Any]] = domain_pool.ensure_seed_domains()
        self._patches: contextlib.ExitStack | None = None

    def __enter__(self) -> _FastSoakRuntime:
        stack = contextlib.ExitStack()
        stack.enter_context(patch.object(oed_orchestrator, "metrics_tail", self.metrics_tail))
        stack.enter_context(patch.object(oed_orchestrator, "plateau", self.plateau))
        stack.enter_context(patch.object(oed_orchestrator, "novelty_drop", self.novelty_drop))
        stack.enter_context(patch.object(oed_orchestrator, "concentration", self.concentration))
        stack.enter_context(patch.object(oed_orchestrator, "load_evaluations", self.load_evaluations))
        stack.enter_context(patch.object(oed_orchestrator, "load_exploration_strategies", self.load_exploration_strategies))
        stack.enter_context(patch.object(oed_orchestrator, "load_strategy_of_strategy", self.load_strategy_of_strategy))
        stack.enter_context(patch.object(oed_orchestrator, "ensure_seed_domains", self.ensure_seed_domains))
        stack.enter_context(patch.object(oed_orchestrator, "get_domain", self.get_domain))
        stack.enter_context(patch.object(oed_orchestrator, "register_domain", self.register_domain))
        stack.enter_context(patch.object(artifact_civilization, "_register_artifact", self.register_artifact))
        stack.enter_context(patch.object(artifact_civilization, "_register_policy", self.register_policy))
        stack.enter_context(patch.object(artifact_civilization, "_register_evaluation", self.register_evaluation))
        stack.enter_context(patch.object(artifact_civilization, "_register_allocator", self.register_allocator))
        stack.enter_context(patch.object(artifact_civilization, "_register_exploration_strategy", self.register_exploration_strategy))
        stack.enter_context(patch.object(artifact_civilization, "_register_strategy_of_strategy", self.register_strategy_of_strategy))
        stack.enter_context(patch.object(domain_router, "domain_names", self.domain_names))
        stack.enter_context(patch.object(metrics_history, "tail", self.metrics_tail))
        stack.enter_context(patch.object(metrics_history, "plateau", self.plateau))
        stack.enter_context(patch.object(metrics_history, "novelty_drop", self.novelty_drop))
        stack.enter_context(patch.object(metrics_history, "failure_spike", self.failure_spike))
        stack.enter_context(patch.object(pressure_engine, "plateau", self.plateau))
        stack.enter_context(patch.object(pressure_engine, "novelty_drop", self.novelty_drop))
        stack.enter_context(patch.object(pressure_engine, "failure_spike", self.failure_spike))
        stack.enter_context(patch.object(pressure_engine, "concentration", self.concentration))
        stack.enter_context(patch.object(lineage_graph, "concentration", self.concentration))
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
        rows = self.metrics_tail(window)
        return [float(row.get(key, 0.0)) for row in rows if isinstance(row, Mapping)]

    def metrics_tail(self, n: int = 200) -> list[dict[str, Any]]:
        if n <= 0:
            return []
        if n >= len(self.metric_history):
            return list(self.metric_history)
        return list(collections.deque(self.metric_history, maxlen=n))

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

    def failure_spike(self, window: int = 50, threshold: float = 0.2) -> bool:
        vals = self._metric_values(window, "fail_rate")
        if not vals:
            return False
        return (sum(vals) / len(vals)) > threshold

    def concentration(self) -> float:
        if self.total_edges <= 0:
            return 0.0
        top = max(self.parent_counts.values(), default=0)
        return top / self.total_edges if self.total_edges else 0.0

    def load_evaluations(self) -> list[dict[str, Any]]:
        return self.evaluation_rows

    def load_exploration_strategies(self) -> list[dict[str, Any]]:
        return self.strategy_rows

    def load_strategy_of_strategy(self) -> list[dict[str, Any]]:
        return self.strategy_of_strategy_rows

    def ensure_seed_domains(self) -> dict[str, dict[str, Any]]:
        return self.domain_pool

    def domain_names(self) -> list[str]:
        return sorted(self.domain_pool)

    def get_domain(self, name: str) -> dict[str, Any] | None:
        return self.domain_pool.get(str(name))

    def register_domain(self, name: str, genome: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if str(name) not in self.domain_pool and len(self.domain_pool) >= 8:
            fallback = next(reversed(self.domain_pool.values()))
            return dict(fallback)
        row = {"name": str(name), "genome": dict(genome) if isinstance(genome, Mapping) else genome}
        self.domain_pool[str(name)] = row
        return dict(row)

    def register_artifact(self, data: Any, parent: str | None = None, **kwargs: Any) -> str:
        artifact_id = str(uuid.uuid4())
        if parent:
            self.parent_counts[str(parent)] += 1
            self.total_edges += 1
        return artifact_id

    def register_policy(self, policy: Mapping[str, Any], pressure: Mapping[str, float], score: float, *, parent: str | None = None) -> str:
        artifact_id = str(uuid.uuid4())
        if parent:
            self.parent_counts[str(parent)] += 1
            self.total_edges += 1
        return artifact_id

    def register_evaluation(self, evaluation: Mapping[str, Any], pressure: Mapping[str, float], score: float, *, parent: str | None = None) -> str:
        artifact_id = str(uuid.uuid4())
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

    def register_allocator(
        self,
        allocator: Mapping[str, Any],
        pressure: Mapping[str, float],
        workers: int,
        budgets: Mapping[str, float],
        *,
        parent: str | None = None,
    ) -> str:
        artifact_id = str(uuid.uuid4())
        if parent:
            self.parent_counts[str(parent)] += 1
            self.total_edges += 1
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
        artifact_id = str(uuid.uuid4())
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

    def register_strategy_of_strategy(
        self,
        strategy_of_strategy: Mapping[str, Any],
        pressure: Mapping[str, float],
        market: Mapping[str, float],
        ecology: Mapping[str, float],
        score: float,
        *,
        parent: str | None = None,
    ) -> str:
        artifact_id = str(uuid.uuid4())
        self.strategy_of_strategy_rows.append(
            {
                "id": artifact_id,
                "parent": parent,
                "strategy_of_strategy": dict(strategy_of_strategy),
                "pressure": dict(pressure),
                "market": dict(market),
                "ecology": dict(ecology),
                "score": float(score),
            }
        )
        return artifact_id

    def save(self, kind: str, payload: Any) -> None:
        if kind not in {
            "pressure",
            "stabilized_pressure",
            "quest",
            "policy",
            "guard",
            "repair",
            "resource_allocation",
            "exploration_economy_state",
            "civilization_state",
            "civilization_stability",
            "exploration_cycle",
            "meta_exploration",
        }:
            return
        self.archive_writer.append({"kind": kind, "payload": payload})

    def remember(self, kind: str, payload: Any) -> None:
        if kind not in {
            "pressure_snapshot",
            "quest_artifact",
            "policy_artifact",
            "repair_artifact",
            "resource_allocation",
            "civilization_state",
            "civilization_stability",
            "meta_exploration_artifact",
            "exploration_cycle",
        }:
            return
        self.memory_writer.append({"kind": kind, "payload": payload})

    def append_metrics_snapshot(self, tick: int, metrics: Mapping[str, float], state: Mapping[str, Any]) -> None:
        row = _fast_metrics_row(tick, metrics, state)
        self.metric_history.append(row)
        self.metrics_writer.append(row)

    def record_histories(self, metrics: Mapping[str, float], state: Mapping[str, Any]) -> None:
        self.guard_history.append(_fast_guard_row(metrics, state))
        cooldown = state.get("cooldown", {})
        if isinstance(cooldown, Mapping):
            self.cooldown_history.append(dict(cooldown))
        routing = state.get("routing", {})
        if isinstance(routing, Mapping):
            self.routing_history.append(dict(routing))
        ecology = state.get("ecology", {})
        if isinstance(ecology, Mapping):
            cached_ecology = dict(ecology)
            self.ecology_history.append(cached_ecology)
            self.latest_ecology = cached_ecology
        civilization_selection = state.get("civilization_selection", {})
        if isinstance(civilization_selection, Mapping):
            self.latest_civilization_selection = dict(civilization_selection)
        population = state.get("population", {})
        if isinstance(population, Mapping):
            population_counts = population.get("population_counts", {})
            if isinstance(population_counts, Mapping):
                self.population_counts.clear()
                for artifact_type, count in population_counts.items():
                    self.population_counts[str(artifact_type)] = int(count)

    def maybe_flush(self, tick: int, total_ticks: int) -> None:
        if tick == total_ticks:
            self.flush()
            return
        if tick % self.flush_every == 0:
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
        self.work_count = 0
        self.exploration_count = 0
        self.cross_domain_count = 0
        self.meta_count = 0
        self.reframing_count = 0
        self.freeze_count = 0
        self.domain_switch_count = 0
        self.strategy_of_strategy_count = 0
        self.governor_interventions = 0
        self.meta_exploration_count = 0
        self.new_domain_count = 0
        self.budget_cycle_count = 0
        self._last_selected_domain: str | None = None
        self.selected_domain_counts: collections.Counter[str] = collections.Counter()
        self.selected_artifact_type_counts: collections.Counter[str] = collections.Counter()
        self.artifact_population_counts: collections.Counter[str] = collections.Counter()
        self.created_domains: set[str] = set()

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
        if qtype == "work":
            self.work_count += 1
        if qtype == "exploration":
            self.exploration_count += 1
        if qtype == "meta":
            self.meta_count += 1
        if qtype == "reframing":
            self.reframing_count += 1
        routing = report.get("routing", {}) if isinstance(report.get("routing"), Mapping) else {}
        selected_domain = str(routing.get("selected_domain", report.get("domain", "default")))
        if selected_domain:
            self.selected_domain_counts[selected_domain] += 1
        if self._last_selected_domain is not None and selected_domain and selected_domain != self._last_selected_domain:
            self.domain_switch_count += 1
        if selected_domain:
            self._last_selected_domain = selected_domain
        if selected_domain and selected_domain != str(report.get("domain", "default")):
            self.cross_domain_count += 1
        civilization_selection = report.get("civilization_selection", {}) if isinstance(report.get("civilization_selection"), Mapping) else {}
        selected_artifact_type = str(civilization_selection.get("selected_artifact_type", ""))
        if selected_artifact_type:
            self.selected_artifact_type_counts[selected_artifact_type] += 1
        if selected_artifact_type == "strategy_of_strategy":
            self.strategy_of_strategy_count += 1
        population = report.get("population", {}) if isinstance(report.get("population"), Mapping) else {}
        population_counts = population.get("population_counts", {}) if isinstance(population.get("population_counts"), Mapping) else {}
        for artifact_type, count in population_counts.items():
            self.artifact_population_counts[str(artifact_type)] = int(count)
        meta_exploration = report.get("meta_exploration", {}) if isinstance(report.get("meta_exploration"), Mapping) else {}
        if meta_exploration:
            self.meta_exploration_count += 1
        domain_creation = meta_exploration.get("domain_creation")
        if isinstance(domain_creation, Mapping) and domain_creation:
            name = str(domain_creation.get("name", ""))
            if name and name not in self.created_domains:
                self.created_domains.add(name)
                self.new_domain_count += 1
        governance = report.get("governance", {}) if isinstance(report.get("governance"), Mapping) else {}
        if bool(governance.get("intervention")):
            self.governor_interventions += 1
        exploration_cycle = report.get("exploration_cycle", {}) if isinstance(report.get("exploration_cycle"), Mapping) else {}
        if bool(exploration_cycle.get("exhausted")):
            self.budget_cycle_count += 1
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
            "work_count": self.work_count,
            "exploration_count": self.exploration_count,
            "cross_domain_count": self.cross_domain_count,
            "domain_switch_count": self.domain_switch_count,
            "selected_domain_counts": dict(self.selected_domain_counts),
            "selected_artifact_type_counts": dict(self.selected_artifact_type_counts),
            "artifact_population_counts": dict(self.artifact_population_counts),
            "meta_count": self.meta_count,
            "reframing_count": self.reframing_count,
            "strategy_of_strategy_count": self.strategy_of_strategy_count,
            "meta_exploration_count": self.meta_exploration_count,
            "new_domain_count": self.new_domain_count,
            "created_domains": sorted(self.created_domains),
            "governor_interventions": self.governor_interventions,
            "budget_cycle_count": self.budget_cycle_count,
            "meta_share": round(self.meta_count / count, 4),
            "exploration_share": round(self.exploration_count / count, 4),
            "freeze_count": self.freeze_count,
        }


def _next_state(
    tick: int,
    result: Mapping[str, Any],
    *,
    workers: int,
    worker_cap: int,
    domain: str,
) -> dict[str, Any]:
    return {
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
        "ecology": result.get("ecology", {}),
        "strategy_of_strategy": result.get("strategy_of_strategy", {}),
        "exploration_cycle": result.get("exploration_cycle", {}),
        "meta_exploration": result.get("meta_exploration", {}),
        "civilization_selection": result.get("civilization_selection", {}),
        "population": result.get("population", {}),
        "governance": result.get("governance", {}),
        "economy": result.get("economy", {}),
        "exploration_economy_state": result.get("exploration_economy_state", {}),
        "resource_allocation": result.get("resource_allocation", {}),
        "civilization_state": result.get("civilization_state", {}),
        "civilization_stability": result.get("civilization_stability", {}),
        "guard": result.get("guard", {}),
        "cooldown": result.get("cooldown", {}),
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
    persist_soak_snapshots = fast_runtime is None

    with fast_runtime or contextlib.nullcontext():
        total_ticks = len(sequence)
        guard_history: collections.deque[dict[str, Any]] | None = None
        if fast_runtime is None:
            guard_history = collections.deque(maxlen=total_ticks or None)
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
                next_state = _next_state(tick, result, workers=workers, worker_cap=worker_cap, domain=domain)
                if persist_soak_snapshots:
                    save("soak_snapshot", next_state)
                    remember("soak_snapshot", next_state)
                return next_state

            if fail_open:
                next_state = guarded_step(_step, state) or state
            else:
                next_state = _step(state)
            state = next_state if isinstance(next_state, dict) else _next_state(tick, next_state, workers=workers, worker_cap=worker_cap, domain=domain)
            if fast_runtime is not None:
                fast_runtime.record_histories(metrics, state)
                state["guard"] = detect_guard_state(fast_runtime.guard_history)
                fast_runtime.guard_history[-1]["guard"] = state["guard"]
                fast_runtime.maybe_flush(tick, total_ticks)
            else:
                assert guard_history is not None
                guard_history.append({**dict(metrics), **state})
                state["guard"] = detect_guard_state(guard_history)
            reports.append(state if fast_runtime is not None else dict(state))
            summary.update(state)
    return SoakResult(reports, summary.summary())
