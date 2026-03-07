from __future__ import annotations

from collections import Counter
from typing import Any, Mapping


_ALLOWED_TYPES = frozenset({"artifact", "policy", "evaluation", "strategy", "output", "memory"})


def hydration_policy(civilization: Mapping[str, Any], safety: Mapping[str, Any] | None = None) -> dict[str, Any]:
    state = dict(civilization or {})
    safety_state = dict(safety or {})
    distribution = state.get("foreign_origin_distribution", {})
    counts = Counter({str(key): int(value) for key, value in dict(distribution).items()}) if isinstance(distribution, Mapping) else Counter()
    total = sum(counts.values()) or 1
    concentration = max(counts.values(), default=0) / total
    return {
        "allowed": (sum(counts.values()) < 4 or concentration < 0.78) and float(safety_state.get("federation_overload_score", 0.0)) < 0.85,
        "max_hydrated_artifacts_per_window": 12,
        "max_hydration_depth": 3,
        "origin_concentration_limit": 0.78,
        "artifact_type_allowlist": sorted(_ALLOWED_TYPES),
        "foreign_origin_concentration": round(concentration, 4),
    }


__all__ = ["hydration_policy"]
