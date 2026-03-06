from __future__ import annotations

import copy
import random
from typing import Mapping


DEFAULT_EVALUATION = {
    "score": 0.32,
    "novelty": 0.18,
    "diversity": 0.15,
    "efficiency": 0.14,
    "repair_burden": 0.11,
    "lineage_penalty": 0.1,
}


def _clamp(value: float, low: float = 0.05, high: float = 0.55) -> float:
    return max(low, min(high, float(value)))


def _normalize(weights: Mapping[str, float]) -> dict[str, float]:
    bounded = {key: _clamp(value) for key, value in weights.items()}
    total = sum(bounded.values()) or 1.0
    out = {key: round(value / total, 4) for key, value in bounded.items()}
    correction = round(1.0 - sum(out.values()), 4)
    last_key = next(reversed(out))
    out[last_key] = round(out[last_key] + correction, 4)
    return out


def evolve_evaluation(
    current: Mapping[str, float] | None = None,
    pressure: Mapping[str, float] | None = None,
    market_state: Mapping[str, float] | None = None,
) -> dict[str, float]:
    pressure = dict(pressure or {})
    market_state = dict(market_state or {})
    weights = copy.deepcopy(dict(current or DEFAULT_EVALUATION))
    for key in DEFAULT_EVALUATION:
        value = float(weights.get(key, DEFAULT_EVALUATION[key]))
        delta = random.uniform(-0.025, 0.025)
        if key == "novelty":
            delta += 0.05 * float(pressure.get("novelty_pressure", 0.0))
        elif key == "diversity":
            delta += 0.04 * float(pressure.get("diversity_pressure", 0.0))
        elif key == "efficiency":
            delta += 0.04 * float(pressure.get("efficiency_pressure", 0.0))
        elif key == "repair_burden":
            delta += 0.05 * float(pressure.get("repair_pressure", 0.0))
        elif key == "lineage_penalty":
            delta += 0.05 * float(pressure.get("lineage_pressure", 0.0))
        elif key == "score":
            delta += 0.04 * float(market_state.get("selection_bias", 0.0))
        weights[key] = _clamp(value + delta)
    return _normalize(weights)
