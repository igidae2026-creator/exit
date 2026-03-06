from __future__ import annotations

from typing import Mapping


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def score_candidate(
    candidate: Mapping[str, float],
    weights: Mapping[str, float] | None = None,
) -> float:
    weights = dict(weights or {})
    score = float(candidate.get("score", 0.0))
    novelty = float(candidate.get("novelty", 0.0))
    diversity = float(candidate.get("diversity", 0.0))
    efficiency = 1.0 - float(candidate.get("cost", 0.0))
    repair_burden = 1.0 - float(candidate.get("repair_burden", 0.0))
    total = (
        float(weights.get("score", 0.45)) * score
        + float(weights.get("novelty", 0.20)) * novelty
        + float(weights.get("diversity", 0.20)) * diversity
        + float(weights.get("efficiency", 0.10)) * efficiency
        + float(weights.get("repair", 0.05)) * repair_burden
    )
    return round(_clamp(total), 6)
