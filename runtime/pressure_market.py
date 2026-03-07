from __future__ import annotations

from typing import Mapping


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def market(pressure: Mapping[str, float]) -> dict[str, float]:
    novelty = float(pressure.get("novelty_pressure", 0.0))
    diversity = float(pressure.get("diversity_pressure", 0.0))
    repair = float(pressure.get("repair_pressure", 0.0))
    efficiency = float(pressure.get("efficiency_pressure", 0.0))
    domain_shift = float(pressure.get("domain_shift_pressure", 0.0))
    reframing = float(pressure.get("reframing_pressure", 0.0))

    raw = {
        "mutation_bias": 0.35 + (0.25 * novelty) + (0.20 * diversity),
        "selection_bias": 0.35 + (0.20 * diversity) + (0.10 * efficiency),
        "archive_bias": 0.25 + (0.20 * repair) + (0.15 * reframing),
        "repair_bias": 0.20 + (0.45 * repair) + (0.10 * efficiency),
        "domain_budget_bias": 0.20 + (0.35 * domain_shift) + (0.20 * reframing),
    }
    clamped = {key: _clamp(value, 0.0, 1.0) for key, value in raw.items()}
    total = sum(clamped.values()) or 1.0
    keys = list(clamped.keys())
    normalized = {key: round(clamped[key] / total, 6) for key in keys[:-1]}
    remainder = round(1.0 - sum(normalized.values()), 6)
    normalized[keys[-1]] = max(0.0, remainder)
    return normalized
