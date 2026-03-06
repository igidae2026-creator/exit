"""METAOS core runtime loop.

Pipeline order:
signal -> strategy -> artifact -> metrics -> mutation -> quest -> decision -> log
"""

from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping

from metaos.observer.pressure_engine import pressure
from metaos.policy.evolve_policy import evolve
from metaos.registry.artifact_registry import register
from metaos.runtime.oed_orchestrator import step as oed_step
from metaos.runtime.quota_allocator import allocate
from metaos.runtime.quest_system import spawn_quest


StageHandler = Callable[[MutableMapping[str, Any]], Any]

DEFAULT_STAGE_ORDER: List[str] = [
    "signal",
    "strategy",
    "artifact",
    "metrics",
    "mutation",
    "quest",
    "decision",
    "log",
]


@dataclass(slots=True)
class LoopConfig:
    """Config for an infinite, tick-driven runtime loop."""

    tick_seconds: float = 1.0
    stage_order: Iterable[str] = field(default_factory=lambda: tuple(DEFAULT_STAGE_ORDER))


class RuntimeLoop:
    """Runs stage handlers in a fixed order on every tick."""

    def __init__(self, handlers: Mapping[str, StageHandler], config: LoopConfig | None = None) -> None:
        self.config = config or LoopConfig()
        self._stage_order = list(self.config.stage_order)
        self._handlers: Dict[str, StageHandler] = dict(handlers)

    def run_forever(self) -> None:
        """Run the pipeline forever, sleeping for tick_seconds between iterations."""
        while True:
            started = time.monotonic()
            self.step()
            elapsed = time.monotonic() - started
            remaining = self.config.tick_seconds - elapsed
            if remaining > 0:
                time.sleep(remaining)

    def step(self) -> Dict[str, Any]:
        """Run one full tick with error isolation per stage."""
        context: Dict[str, Any] = {
            "tick_started_at": time.time(),
            "stage_results": {},
            "errors": [],
        }

        for stage_name in self._stage_order:
            handler = self._handlers.get(stage_name, _noop_handler)
            if stage_name == "log":
                context["tick_completed_at"] = time.time()
            try:
                context["stage_results"][stage_name] = handler(context)
            except Exception as exc:  # noqa: BLE001 - isolate stage faults
                context["errors"].append(
                    {
                        "stage": stage_name,
                        "error": f"{type(exc).__name__}: {exc}",
                        "traceback": traceback.format_exc(),
                    }
                )
                context["stage_results"][stage_name] = None

        context.setdefault("tick_completed_at", time.time())
        return context


def _noop_handler(_: MutableMapping[str, Any]) -> None:
    return None


def oed_extension(metrics: Mapping[str, float], policy: MutableMapping[str, float], workers: int) -> tuple[dict[str, Any], dict[str, float], int]:
    p = pressure(metrics)
    q = spawn_quest(p)
    workers = allocate(p, workers)
    policy = evolve(policy, p)
    register(
        {"quest": q, "policy": dict(policy), "pressure": p, "workers": workers},
        "root",
        "quest",
        score=float(metrics.get("score", 0.0)),
        novelty=float(metrics.get("novelty", 0.0)),
        diversity=float(metrics.get("diversity", 0.0)),
        cost=float(metrics.get("cost", 0.0)),
        quest=q,
        policy=policy,
    )
    return q, policy, workers


def oed_phase2(
    metrics: Mapping[str, float],
    policy: Mapping[str, float] | None,
    workers: int,
    domain: str = "default",
    parent: str | None = None,
) -> dict[str, Any]:
    return oed_step(metrics=metrics, policy=policy, workers=workers, domain=domain, parent=parent)
