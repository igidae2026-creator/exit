from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, float(value))), 4)


def _evaluation_regime(row: Mapping[str, Any]) -> str:
    evaluation = row.get("evaluation", {}) if isinstance(row.get("evaluation"), Mapping) else {}
    regime = str(evaluation.get("regime", row.get("evaluation_regime", ""))).strip()
    if regime:
        return regime
    novelty = float(evaluation.get("novelty_weight", 0.0) or 0.0)
    diversity = float(evaluation.get("diversity_weight", 0.0) or 0.0)
    efficiency = float(evaluation.get("efficiency_weight", 0.0) or 0.0)
    if novelty >= max(diversity, efficiency):
        return "novelty"
    if diversity >= efficiency:
        return "diversity"
    return "efficiency"


def evaluation_lifecycle(history: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows = [row for row in history if isinstance(row, Mapping) and isinstance(row.get("evaluation"), Mapping)]
    regimes: Counter[str] = Counter(_evaluation_regime(row) for row in rows if _evaluation_regime(row))
    active_window = rows[-16:]
    active_counts: Counter[str] = Counter(_evaluation_regime(row) for row in active_window if _evaluation_regime(row))
    active = sorted(name for name, count in active_counts.items() if count > 0)
    dormant = sorted(name for name, count in regimes.items() if count > 0 and name not in set(active))
    retired = sorted(name for name, count in regimes.items() if count <= 1 and name not in set(active))
    total = sum(active_counts.values()) or 1
    active_distribution = {
        key: round(value / total, 4)
        for key, value in sorted(active_counts.items())
    }
    dominance = max(active_distribution.values(), default=0.0)
    diversity = _clamp((1.0 - dominance) + (0.25 * min(1.0, len(active) / 4.0))) if active else 0.0
    prior_window = rows[-32:-16]
    prior_active = {_evaluation_regime(row) for row in prior_window if _evaluation_regime(row)}
    reactivated = sorted(name for name in active if name in prior_active and active_counts.get(name, 0) > 0)
    retired_now = sorted(name for name in prior_active if name not in set(active))
    return {
        "evaluation_generations": len(regimes),
        "active_evaluation_generations": len(active),
        "dormant_evaluation_generations": len(dormant),
        "retired_evaluation_generations": len(retired),
        "active_evaluation_distribution": active_distribution,
        "evaluation_diversity": diversity,
        "evaluation_dominance_index": round(dominance, 4),
        "evaluation_retirement_rate": _clamp(len(retired_now) / max(1.0, float(len(prior_active) or 1))),
        "evaluation_reactivation_rate": _clamp(len(reactivated) / max(1.0, float(len(active) or 1))),
        "active_regimes": active,
        "dormant_regimes": dormant,
        "retired_regimes": retired,
    }


__all__ = ["evaluation_lifecycle"]
