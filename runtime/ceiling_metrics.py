from __future__ import annotations

import math
from collections import Counter
from typing import Any, Mapping, Sequence


CEILING_METRICS = (
    "threshold_crossing_score",
    "breakout_acceleration_score",
    "tail_yield_score",
    "dominant_lock_in_risk",
    "resurrection_potential",
    "portfolio_concentration_risk",
    "policy_staleness_score",
    "exploration_entropy",
    "lineage_entropy",
    "innovation_density",
)


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 6)


def _float(mapping: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(mapping.get(key, default))
    except Exception:
        return default


def _entropy(values: Sequence[str]) -> float:
    if not values:
        return 0.0
    counts = Counter(values)
    if len(counts) <= 1:
        return 0.0
    total = float(sum(counts.values()) or 1.0)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log(p)
    return _clamp(entropy / max(math.log(len(counts)), 1e-6))


def compute_ceiling_metrics(
    context: Mapping[str, Any],
    history: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, float]:
    rows = list(history or [])
    recent_scores = [float(row.get("score", 0.0)) for row in rows[-16:] if isinstance(row.get("score"), (int, float))]
    prior_scores = [float(row.get("score", 0.0)) for row in rows[-32:-16] if isinstance(row.get("score"), (int, float))]
    score = _float(context, "score", recent_scores[-1] if recent_scores else 0.0)
    novelty = _float(context, "novelty")
    diversity = _float(context, "diversity")
    quality = _float(context, "quality", score)
    dominant_share = _float(context, "dominance_index", _float(context, "lineage_concentration"))
    policy_stagnation = _float(context, "policy_stagnation", 1.0 - novelty)
    dormant_share = _float(context, "dormant_lineage_count") / max(1.0, _float(context, "surviving_lineages", len(set(context.get("lineages", []))) or 1.0))
    threshold = _float(context, "ceiling_threshold", 0.82)
    domains = [str(value) for value in context.get("categories", context.get("domains", [])) if value is not None]
    lineages = [str(value) for value in context.get("lineages", []) if value is not None]
    if not lineages and isinstance(context.get("lineage_population"), Mapping):
        for lineage_id, count in dict(context["lineage_population"]).items():
            lineages.extend([str(lineage_id)] * max(1, int(count)))
    avg_recent = sum(recent_scores) / max(1, len(recent_scores))
    avg_prior = sum(prior_scores) / max(1, len(prior_scores)) if prior_scores else max(0.0, avg_recent - max(0.0, score - avg_recent))
    acceleration = max(0.0, avg_recent - avg_prior)
    tail_yield = max(0.0, len([value for value in recent_scores if value >= threshold]) / max(1, len(recent_scores)))
    innovation_density = max(0.0, ((novelty + diversity + quality) / 3.0) * (1.0 - dominant_share))
    return {
        "threshold_crossing_score": _clamp(max(0.0, (score - threshold) / max(1e-6, 1.0 - threshold))),
        "breakout_acceleration_score": _clamp(acceleration * 4.0),
        "tail_yield_score": _clamp(tail_yield if recent_scores else max(0.0, score - 0.7)),
        "dominant_lock_in_risk": _clamp((0.65 * dominant_share) + (0.35 * max(0.0, 1.0 - diversity))),
        "resurrection_potential": _clamp((0.55 * dormant_share) + (0.45 * novelty)),
        "portfolio_concentration_risk": _clamp((0.60 * dominant_share) + (0.25 * max(0.0, 1.0 - _entropy(domains))) + (0.15 * max(0.0, 1.0 - diversity))),
        "policy_staleness_score": _clamp(policy_stagnation),
        "exploration_entropy": _clamp(_entropy(domains)),
        "lineage_entropy": _clamp(_entropy(lineages)),
        "innovation_density": _clamp(innovation_density),
    }


def latest_ceiling_metrics(history: Sequence[Mapping[str, Any]] | None) -> dict[str, float]:
    rows = list(history or [])
    for row in reversed(rows):
        if all(key in row for key in CEILING_METRICS):
            return {key: _clamp(float(row.get(key, 0.0))) for key in CEILING_METRICS}
    if rows:
        return compute_ceiling_metrics(rows[-1], history=rows)
    return {key: 0.0 for key in CEILING_METRICS}


__all__ = ["CEILING_METRICS", "compute_ceiling_metrics", "latest_ceiling_metrics"]
