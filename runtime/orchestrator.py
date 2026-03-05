"""METAOS runtime orchestrator.

Builds the default core loop with minimal dependencies and a configurable tick.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, MutableMapping

if __package__ in (None, ""):
    # Support direct execution: `python runtime/orchestrator.py`.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.loop import DEFAULT_STAGE_ORDER, LoopConfig, RuntimeLoop


@dataclass(slots=True)
class OrchestratorConfig:
    tick_seconds: float = 1.0

    @classmethod
    def from_env(cls) -> "OrchestratorConfig":
        raw_tick = os.getenv("METAOS_TICK_SECONDS", "1.0")
        try:
            tick = float(raw_tick)
        except ValueError:
            tick = 1.0
        if tick <= 0:
            tick = 1.0
        return cls(tick_seconds=tick)


class Orchestrator:
    def __init__(self, config: OrchestratorConfig | None = None) -> None:
        self.config = config or OrchestratorConfig.from_env()
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

    def run(self) -> None:
        self._loop.run_forever()

    # Stage handlers. Defaults are intentionally small and deterministic.
    def signal(self, ctx: MutableMapping[str, Any]) -> Dict[str, Any]:
        return {"timestamp": time.time()}

    def strategy(self, ctx: MutableMapping[str, Any]) -> Dict[str, Any]:
        signal_data = _stage_result(ctx, "signal")
        return {"mode": "explore", "signal": signal_data}

    def artifact(self, ctx: MutableMapping[str, Any]) -> Dict[str, Any]:
        strategy_data = _stage_result(ctx, "strategy")
        return {"strategy_mode": strategy_data.get("mode", "unknown")}

    def metrics(self, ctx: MutableMapping[str, Any]) -> Dict[str, Any]:
        return {
            "error_count": len(ctx.get("errors", [])),
            "stage_count": len(ctx.get("stage_results", {})),
        }

    def mutation(self, ctx: MutableMapping[str, Any]) -> Dict[str, Any]:
        metrics_data = _stage_result(ctx, "metrics")
        return {"mutated": metrics_data.get("error_count", 0) == 0}

    def quest(self, ctx: MutableMapping[str, Any]) -> Dict[str, Any]:
        mutation_data = _stage_result(ctx, "mutation")
        return {"next": "continue" if mutation_data.get("mutated") else "stabilize"}

    def decision(self, ctx: MutableMapping[str, Any]) -> Dict[str, Any]:
        quest_data = _stage_result(ctx, "quest")
        return {"action": quest_data.get("next", "continue")}

    def log(self, ctx: MutableMapping[str, Any]) -> Dict[str, Any]:
        payload = {
            "tick_started_at": ctx.get("tick_started_at"),
            "tick_completed_at": ctx.get("tick_completed_at"),
            "errors": ctx.get("errors", []),
            "decision": _stage_result(ctx, "decision"),
        }
        print(json.dumps(payload, separators=(",", ":"), ensure_ascii=True), flush=True)
        return {"logged": True}


def _stage_result(ctx: MutableMapping[str, Any], stage: str) -> Dict[str, Any]:
    stage_results = ctx.get("stage_results", {})
    value = stage_results.get(stage)
    return value if isinstance(value, dict) else {}


def run() -> None:
    Orchestrator().run()


if __name__ == "__main__":
    run()
