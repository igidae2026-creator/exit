from __future__ import annotations

from typing import Any, Mapping, Sequence

from signal.pressure import pressure_frame

from metaos.runtime.resource_allocator import allocate


CANONICAL_PRESSURES = (
    "novelty_pressure",
    "diversity_pressure",
    "efficiency_pressure",
    "repair_pressure",
    "domain_shift_pressure",
    "reframing_pressure",
)


def compute_pressure(
    metrics: Mapping[str, float],
    *,
    history: Sequence[Mapping[str, Any]] | None = None,
    guard: Mapping[str, Any] | None = None,
    ecology: Mapping[str, Any] | None = None,
    population: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    frame = pressure_frame(metrics, history=history, guard=guard)
    pressure = {key: float(frame["pressure"].get(key, 0.0)) for key in CANONICAL_PRESSURES}
    stabilized = {key: float(frame["stabilized_pressure"].get(key, 0.0)) for key in CANONICAL_PRESSURES}
    allocation = allocate(stabilized, ecology or {}, population or {})
    return {
        "pressure": pressure,
        "stabilized_pressure": stabilized,
        "market": dict(frame["market"]),
        "mutation_bias": float(frame["market"].get("mutation_bias", 0.0)),
        "selection_bias": float(frame["market"].get("selection_bias", 0.0)),
        "resource_allocation": allocation,
    }


__all__ = ["CANONICAL_PRESSURES", "compute_pressure"]
