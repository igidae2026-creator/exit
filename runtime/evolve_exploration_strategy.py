from __future__ import annotations

import copy
import random
from typing import Mapping


DEFAULT_STRATEGY = {
    "exploration_mode": "balanced",
    "mutation_bias_profile": 0.5,
    "replay_bias_profile": 0.5,
    "domain_shift_bias": 0.35,
}


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, float(value))), 4)


def evolve_strategy(
    current: Mapping[str, float | str] | None = None,
    pressure: Mapping[str, float] | None = None,
    market_state: Mapping[str, float] | None = None,
) -> dict[str, float | str]:
    pressure = dict(pressure or {})
    market_state = dict(market_state or {})
    strategy = copy.deepcopy(dict(current or DEFAULT_STRATEGY))

    novelty = float(pressure.get("novelty_pressure", 0.0))
    repair = float(pressure.get("repair_pressure", 0.0))
    domain_shift = float(pressure.get("domain_shift_pressure", 0.0))
    reframing = float(pressure.get("reframing_pressure", 0.0))

    if repair >= 0.75:
        mode = "stabilize"
    elif domain_shift >= 0.7 or reframing >= 0.7:
        mode = "reframe"
    elif novelty >= 0.65:
        mode = "expand"
    else:
        mode = "balanced"

    strategy["exploration_mode"] = mode
    strategy["mutation_bias_profile"] = _clamp(
        float(strategy.get("mutation_bias_profile", 0.5))
        + random.uniform(-0.04, 0.04)
        + 0.08 * novelty
        + 0.05 * float(market_state.get("mutation_bias", 0.0))
    )
    strategy["replay_bias_profile"] = _clamp(
        float(strategy.get("replay_bias_profile", 0.5))
        + random.uniform(-0.04, 0.04)
        + 0.06 * float(market_state.get("selection_bias", 0.0))
        - 0.05 * repair
    )
    strategy["domain_shift_bias"] = _clamp(
        float(strategy.get("domain_shift_bias", 0.35))
        + random.uniform(-0.04, 0.04)
        + 0.08 * domain_shift
        + 0.05 * reframing
    )
    return strategy
