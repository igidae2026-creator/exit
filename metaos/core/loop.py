from __future__ import annotations

from typing import Mapping

from core.loop import LoopConfig, RuntimeLoop, oed_extension
from metaos.runtime.oed_orchestrator import step as oed_step


def oed_phase2(
    metrics: Mapping[str, float],
    policy: Mapping[str, float] | None,
    workers: int,
    domain: str = "default",
    parent: str | None = None,
) -> dict[str, object]:
    return oed_step(metrics=metrics, policy=policy, workers=workers, domain=domain, parent=parent)


__all__ = ["LoopConfig", "RuntimeLoop", "oed_extension", "oed_phase2"]
