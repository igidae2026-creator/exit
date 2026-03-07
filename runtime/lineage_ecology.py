from __future__ import annotations

from collections import Counter
from math import log
from typing import Any, Mapping, Sequence


def assess_lineages(
    lineage_rows: Sequence[Mapping[str, Any]],
    *,
    diversity_floor: int = 2,
) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    recent_counts: Counter[str] = Counter()
    merge_candidates = 0
    for row in lineage_rows:
        lineage_id = str(
            row.get("lineage_id")
            or row.get("selected_domain")
            or row.get("domain")
            or row.get("artifact_id")
            or ""
        )
        if lineage_id:
            weight = int(row.get("count", 1) or 1)
            counts[lineage_id] += max(1, weight)
            recent_counts[lineage_id] += 1
            if bool(row.get("merge_candidate")):
                merge_candidates += 1
    total = sum(counts.values()) or 1
    dominant = max(counts.values(), default=0)
    surviving = len(counts)
    concentration = round(dominant / total, 4)
    lineage_survival_rate = round(surviving / max(1, int(diversity_floor)), 4)
    lineage_diversity = round(min(1.0, surviving / max(1.0, total / 2.0)), 4)
    proportions = [value / total for value in counts.values() if value > 0]
    shannon = -sum(value * log(value) for value in proportions) if proportions else 0.0
    effective_diversity = round(min(1.0, shannon / max(log(max(2, surviving)), 1e-6)), 4) if surviving > 1 else 0.0
    dormant = sorted(name for name, value in counts.items() if value <= 1)
    zombie = sorted(name for name, value in counts.items() if value == 1 and recent_counts.get(name, 0) == 1)
    fake_diversity = surviving >= int(diversity_floor) and effective_diversity < 0.35
    actions: list[str] = []
    if concentration >= 0.7:
        actions.append("selection_penalty_on_dominant_lineage")
    if surviving < int(diversity_floor) or fake_diversity:
        actions.append("increase_diversity_pressure")
        actions.append("explore_underrepresented_lineages")
    if zombie:
        actions.append("archive_dormant_lineages")
    branch_rate = round(min(1.0, max(0.0, surviving / max(1.0, float(total)))), 4)
    merge_rate = round(min(1.0, merge_candidates / max(1.0, float(len(lineage_rows) or 1))), 4)
    return {
        "surviving_lineages": surviving,
        "lineages": dict(counts),
        "diversity_floor": int(diversity_floor),
        "diversity_floor_ok": surviving >= int(diversity_floor),
        "single_lineage_dominance": concentration > 0.85,
        "lineage_concentration": concentration,
        "lineage_diversity": lineage_diversity,
        "diversity_index": lineage_diversity,
        "lineage_survival_rate": lineage_survival_rate,
        "dominance_index": concentration,
        "effective_lineage_diversity": effective_diversity,
        "active_lineage_count": len([name for name, value in counts.items() if value > 1]),
        "dormant_lineage_count": len(dormant),
        "dormant_lineages": dormant,
        "zombie_lineages": zombie,
        "fake_diversity": fake_diversity,
        "lineage_actions": actions[:8],
        "branch_rate": branch_rate,
        "merge_rate": merge_rate,
        "stable": surviving >= int(diversity_floor) and concentration < 0.85 and not fake_diversity,
    }


def lineage_status(lineage_rows: Sequence[Mapping[str, Any]], *, diversity_floor: int = 2) -> dict[str, Any]:
    return assess_lineages(lineage_rows, diversity_floor=diversity_floor)


__all__ = ["assess_lineages", "lineage_status"]
