from __future__ import annotations

from typing import Any, Mapping, Sequence

from metaos.observer.pressure_engine import pressure as raw_pressure
from metaos.runtime.pressure_ecology import stabilize_pressure
from metaos.runtime.pressure_market import market


def pressure_frame(
    metrics: Mapping[str, float],
    *,
    history: Sequence[Mapping[str, Any]] | None = None,
    guard: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, float]]:
    current = raw_pressure(metrics)
    stabilized = stabilize_pressure(current, history=history, guard=guard)
    return {
        "pressure": current,
        "stabilized_pressure": stabilized,
        "market": market(stabilized),
    }

