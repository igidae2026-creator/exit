from __future__ import annotations

from typing import Any, Mapping

from artifact.registry import register_envelope


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, float(value))), 4)


def evolve_strategies(
    current: Mapping[str, Any] | None,
    pressure: Mapping[str, float],
    outcomes: Mapping[str, Any] | None = None,
    *,
    parent: str | None = None,
) -> dict[str, Any]:
    current = dict(current or {})
    pressure = dict(pressure or {})
    outcomes = dict(outcomes or {})
    strategy = {
        "exploration_bias": _clamp(float(current.get("exploration_bias", 0.35)) + 0.18 * float(pressure.get("novelty_pressure", 0.0))),
        "selection_bias": _clamp(float(current.get("selection_bias", 0.3)) + 0.14 * float(pressure.get("diversity_pressure", 0.0))),
        "mutation_bias": _clamp(float(current.get("mutation_bias", 0.3)) + 0.12 * float(pressure.get("domain_shift_pressure", 0.0))),
        "repair_bias": _clamp(float(current.get("repair_bias", 0.2)) + 0.20 * float(pressure.get("repair_pressure", 0.0))),
        "archive_bias": _clamp(float(current.get("archive_bias", 0.2)) + 0.10 * float(outcomes.get("success_rate", 0.0))),
    }
    artifact_id = register_envelope(
        aclass="strategy",
        atype="exploration_strategy",
        spec={"strategy": strategy, "outcomes": outcomes},
        refs={"parents": [parent] if parent else [], "inputs": [], "subjects": [], "context": {"pressure": pressure}},
        provenance={
            "score": float(outcomes.get("success_rate", 0.0)),
            "novelty": float(pressure.get("novelty_pressure", 0.0)),
            "diversity": float(pressure.get("diversity_pressure", 0.0)),
            "efficiency": 1.0 - float(pressure.get("efficiency_pressure", 0.0)),
        },
    )
    return {"artifact_id": artifact_id, "strategy": strategy, "lineage_parent": parent}


__all__ = ["evolve_strategies"]
