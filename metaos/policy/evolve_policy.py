from __future__ import annotations

import copy
import random
from typing import Mapping


DEFAULT = {
    "selection_weight_score": 0.45,
    "selection_weight_novelty": 0.25,
    "selection_weight_diversity": 0.20,
    "selection_weight_efficiency": 0.10,
    "mutation_rate": 0.20,
    "share_threshold": 0.75,
}


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _normalize_selection(policy: dict[str, float]) -> dict[str, float]:
    keys = [
        "selection_weight_score",
        "selection_weight_novelty",
        "selection_weight_diversity",
        "selection_weight_efficiency",
    ]
    bounded = {key: max(0.05, float(policy.get(key, DEFAULT[key]))) for key in keys}
    total = sum(bounded.values()) or 1.0
    normalized = {key: round(bounded[key] / total, 4) for key in keys}
    correction = round(1.0 - sum(normalized.values()), 4)
    normalized[keys[-1]] = round(normalized[keys[-1]] + correction, 4)
    policy.update(normalized)
    return policy


def evolve(policy: Mapping[str, float] | None = None, pressure: Mapping[str, float] | None = None) -> dict[str, float]:
    p = copy.deepcopy(dict(policy or DEFAULT))
    pressure = dict(pressure or {})
    for key in list(p.keys()):
        delta = random.uniform(-0.03, 0.03)
        if key == "mutation_rate":
            delta += 0.05 * float(pressure.get("novelty_pressure", 0.0))
            delta += 0.04 * float(pressure.get("diversity_pressure", 0.0))
            p[key] = clamp(round(float(p[key]) + delta, 4), 0.05, 0.45)
            continue
        if key == "share_threshold":
            delta += 0.03 * float(pressure.get("efficiency_pressure", 0.0))
            p[key] = clamp(round(float(p[key]) + delta, 4), 0.55, 0.90)
            continue
        p[key] = clamp(round(float(p[key]) + delta, 4), 0.05, 0.8)
    return _normalize_selection(p)
