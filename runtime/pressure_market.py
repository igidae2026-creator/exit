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
    competition = float(pressure.get("competition_pressure", 0.0))
    adoption = float(pressure.get("market_adoption_pressure", 0.0))
    platform = float(pressure.get("platform_policy_pressure", 0.0))
    audience = float(pressure.get("audience_feedback_pressure", 0.0))
    volatility = float(pressure.get("environment_volatility", 0.0))
    tail_yield = float(pressure.get("tail_yield_score", 0.0))
    breakout = float(pressure.get("breakout_acceleration_score", 0.0))

    raw = {
        "mutation_bias": 0.28 + (0.18 * novelty) + (0.12 * diversity) + (0.10 * competition) + (0.10 * breakout),
        "selection_bias": 0.28 + (0.16 * diversity) + (0.10 * efficiency) + (0.10 * adoption) + (0.08 * tail_yield),
        "archive_bias": 0.18 + (0.18 * repair) + (0.15 * reframing) + (0.08 * audience),
        "repair_bias": 0.16 + (0.36 * repair) + (0.10 * efficiency) + (0.12 * platform) + (0.08 * volatility),
        "domain_budget_bias": 0.16 + (0.26 * domain_shift) + (0.14 * reframing) + (0.10 * adoption) + (0.10 * competition),
    }
    clamped = {key: _clamp(value, 0.0, 1.0) for key, value in raw.items()}
    total = sum(clamped.values()) or 1.0
    keys = list(clamped.keys())
    normalized = {key: round(clamped[key] / total, 6) for key in keys[:-1]}
    remainder = round(1.0 - sum(normalized.values()), 6)
    normalized[keys[-1]] = max(0.0, remainder)
    return normalized
