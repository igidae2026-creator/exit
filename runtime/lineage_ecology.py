from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence


def assess_lineages(
    lineage_rows: Sequence[Mapping[str, Any]],
    *,
    diversity_floor: int = 2,
) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    for row in lineage_rows:
        lineage_id = str(
            row.get("lineage_id")
            or row.get("selected_domain")
            or row.get("domain")
            or row.get("artifact_id")
            or ""
        )
        if lineage_id:
            counts[lineage_id] += 1
    total = sum(counts.values()) or 1
    dominant = max(counts.values(), default=0)
    surviving = len(counts)
    concentration = round(dominant / total, 4)
    lineage_survival_rate = round(surviving / max(1, int(diversity_floor)), 4)
    lineage_diversity = round(min(1.0, surviving / max(1.0, total / 2.0)), 4)
    return {
        "surviving_lineages": surviving,
        "lineages": dict(counts),
        "diversity_floor": int(diversity_floor),
        "diversity_floor_ok": surviving >= int(diversity_floor),
        "single_lineage_dominance": concentration > 0.85,
        "lineage_concentration": concentration,
        "lineage_diversity": lineage_diversity,
        "lineage_survival_rate": lineage_survival_rate,
        "dominance_index": concentration,
    }


__all__ = ["assess_lineages"]
