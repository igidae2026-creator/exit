"""METAOS core runtime loop.

Canonical pipeline order:
signal -> generate -> evaluate -> select -> mutate -> archive -> repeat
"""

from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping

from runtime.oed_orchestrator import step as oed_step
from runtime.genesis_ceiling import CANONICAL_EXPLORATION_LOOP
from metaos.observer.pressure_engine import pressure as raw_pressure
from runtime.pressure_ecology import stabilize_pressure
from runtime.pressure_market import market
from strategy.quota import quota_frame
from strategy.quest_portfolio import active_quest, quest_slots


StageHandler = Callable[[MutableMapping[str, Any]], Any]

DEFAULT_STAGE_ORDER: List[str] = list(CANONICAL_EXPLORATION_LOOP)

LEGACY_STAGE_ALIASES: Dict[str, tuple[str, ...]] = {
    "signal": ("signal", "metrics"),
    "generate": ("generate", "strategy", "quest"),
    "evaluate": ("evaluate", "artifact"),
    "select": ("select", "decision"),
    "mutate": ("mutate", "mutation"),
    "archive": ("archive", "log"),
    "repeat": ("repeat",),
}


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

    def _handler_for_stage(self, stage_name: str) -> StageHandler:
        for candidate in LEGACY_STAGE_ALIASES.get(stage_name, (stage_name,)):
            handler = self._handlers.get(candidate)
            if handler is not None:
                return handler
        return _noop_handler

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
            handler = self._handler_for_stage(stage_name)
            if stage_name == "repeat":
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
    current_pressure = raw_pressure(metrics)
    stabilized_pressure = stabilize_pressure(current_pressure)
    signal_frame = {"pressure": current_pressure, "stabilized_pressure": stabilized_pressure, "market": market(stabilized_pressure)}
    p = signal_frame["stabilized_pressure"]
    q = active_quest(quest_slots(p))
    quota = quota_frame(p, workers, signal_frame["market"], tick=0)
    workers = int(quota.budgets["effective_workers"])
    policy = dict(policy)
    return q, policy, workers


def oed_phase2(
    metrics: Mapping[str, float],
    policy: Mapping[str, float] | None,
    workers: int,
    domain: str = "default",
    parent: str | None = None,
) -> dict[str, Any]:
    return oed_step(metrics=metrics, policy=policy, workers=workers, domain=domain, parent=parent)
