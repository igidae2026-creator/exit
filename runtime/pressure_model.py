from __future__ import annotations

from typing import Any, Mapping, Sequence

from runtime.civilization_state import civilization_state as build_civilization_state
from runtime.pressure_derivation import pressure_frame as derive_pressure_frame
from runtime.resource_allocator import allocate


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
    civilization = build_civilization_state(state={"metrics": dict(metrics), "guard": dict(guard or {})}, history=list(history or []))
    pressure = derive_pressure_frame(civilization, recent_truth=list(history or []))
    stabilized = dict(pressure)
    allocation = allocate(stabilized, ecology or {}, population or {}, civilization_state=civilization)
    return {
        "pressure": pressure,
        "stabilized_pressure": stabilized,
        "market": {
            "mutation_bias": round(min(1.0, 0.18 + 0.42 * float(stabilized.get("novelty_pressure", 0.0)) + 0.16 * float(stabilized.get("domain_shift_pressure", 0.0))), 4),
            "selection_bias": round(min(1.0, 0.20 + 0.40 * float(stabilized.get("efficiency_pressure", 0.0)) + 0.14 * float(stabilized.get("diversity_pressure", 0.0))), 4),
            "repair_bias": round(min(1.0, 0.18 + 0.50 * float(stabilized.get("repair_pressure", 0.0))), 4),
            "archive_bias": round(min(1.0, 0.15 + 0.40 * float(stabilized.get("reframing_pressure", 0.0))), 4),
        },
        "mutation_bias": round(min(1.0, 0.18 + 0.42 * float(stabilized.get("novelty_pressure", 0.0))), 4),
        "selection_bias": round(min(1.0, 0.20 + 0.40 * float(stabilized.get("efficiency_pressure", 0.0))), 4),
        "resource_allocation": allocation,
        "civilization_state": civilization,
    }


__all__ = ["CANONICAL_PRESSURES", "compute_pressure"]
