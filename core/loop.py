from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping, MutableMapping


StageHandler = Callable[[MutableMapping[str, Any]], Mapping[str, Any] | None]

DEFAULT_STAGE_ORDER = (
    "signal",
    "strategy",
    "artifact",
    "metrics",
    "mutation",
    "quest",
    "decision",
    "log",
)


@dataclass(slots=True)
class LoopConfig:
    tick_seconds: float = 1.0
    stage_order: tuple[str, ...] = DEFAULT_STAGE_ORDER


class RuntimeLoop:
    """Small deterministic runtime loop used by the existing orchestrator."""

    def __init__(
        self,
        handlers: Mapping[str, StageHandler],
        config: LoopConfig | None = None,
    ) -> None:
        self.handlers = dict(handlers)
        self.config = config or LoopConfig()

    def run_once(self, ctx: MutableMapping[str, Any] | None = None) -> MutableMapping[str, Any]:
        state: MutableMapping[str, Any] = {
            "tick_started_at": time.time(),
            "tick_completed_at": None,
            "stage_results": {},
            "errors": [],
        }
        if ctx:
            state.update(ctx)

        stage_results = state["stage_results"]
        errors = state["errors"]

        for stage in self.config.stage_order:
            handler = self.handlers.get(stage)
            if handler is None:
                continue
            try:
                result = handler(state)
                stage_results[stage] = dict(result or {})
            except Exception as exc:
                error = {"stage": stage, "error": str(exc)}
                errors.append(error)
                stage_results[stage] = {"ok": False, "error": str(exc)}

        state["tick_completed_at"] = time.time()
        return state

    def run_forever(self) -> None:
        while True:
            started = time.time()
            self.run_once()
            elapsed = time.time() - started
            sleep_for = max(0.0, self.config.tick_seconds - elapsed)
            if sleep_for > 0:
                time.sleep(sleep_for)
