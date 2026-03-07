from __future__ import annotations

import copy
import random
from typing import Any, Mapping


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, float(value))), 4)


def _pressure_step(pressure: Mapping[str, float] | None) -> float:
    pressure = dict(pressure or {})
    return 0.02 + (
        0.04 * float(pressure.get("domain_shift_pressure", 0.0))
        + 0.04 * float(pressure.get("reframing_pressure", 0.0))
    )


def _merge_value(value_a: Any, value_b: Any, step: float) -> Any:
    if isinstance(value_a, dict) and isinstance(value_b, dict):
        return _merge_mapping(value_a, value_b, step)
    if isinstance(value_a, (int, float)) and isinstance(value_b, (int, float)):
        midpoint = (float(value_a) + float(value_b)) / 2.0
        return _clamp(midpoint + random.uniform(-step, step))
    return copy.deepcopy(value_b if value_b is not None else value_a)


def _merge_mapping(genome_a: Mapping[str, Any], genome_b: Mapping[str, Any], step: float) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for key in sorted(set(genome_a) | set(genome_b)):
        if key in genome_a and key in genome_b:
            merged[key] = _merge_value(genome_a[key], genome_b[key], step)
        elif key in genome_a:
            merged[key] = copy.deepcopy(genome_a[key])
        else:
            merged[key] = copy.deepcopy(genome_b[key])
    return merged


def _mutated_clone(genome: Mapping[str, Any], step: float) -> dict[str, Any]:
    clone = copy.deepcopy(dict(genome))
    for key, value in list(clone.items()):
        if isinstance(value, dict):
            clone[key] = _mutated_clone(value, step)
        elif isinstance(value, (int, float)):
            clone[key] = _clamp(float(value) + random.uniform(-step, step))
    return clone


def recombine(
    genome_a: Mapping[str, Any],
    genome_b: Mapping[str, Any] | None = None,
    pressure: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    step = _pressure_step(pressure)
    if genome_b is None:
        return _mutated_clone(genome_a, step)
    merged = _merge_mapping(dict(genome_a), dict(genome_b), step)
    if "name" not in merged:
        merged["name"] = str(dict(genome_a).get("name", "default"))
    return merged
