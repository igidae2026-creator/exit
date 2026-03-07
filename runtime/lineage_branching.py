from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, float(value))), 4)


def _selected_lineage(row: Mapping[str, Any], default_domain: str) -> str:
    lineage = row.get("lineage", {}) if isinstance(row.get("lineage"), Mapping) else {}
    routing = row.get("routing", {}) if isinstance(row.get("routing"), Mapping) else {}
    return str(
        lineage.get("selected_lineage")
        or routing.get("selected_lineage")
        or routing.get("selected_domain")
        or row.get("domain")
        or default_domain
    )


def lineage_branching(
    history: Sequence[Mapping[str, Any]],
    pressure: Mapping[str, Any],
    *,
    domain: str,
    tick: int,
    evaluation_generations: int = 0,
    policy_stagnation: float = 0.0,
) -> dict[str, Any]:
    rows = list(history or [])
    pressure_state = dict(pressure or {})
    counts: Counter[str] = Counter(_selected_lineage(row, domain) for row in rows[-64:] if _selected_lineage(row, domain))
    total = sum(counts.values()) or 1
    dominant = counts.most_common(1)[0][0] if counts else f"{domain}:root"
    dominance_index = max(counts.values(), default=0) / total
    concentration_streak = 0
    for row in reversed(rows[-24:]):
        if _selected_lineage(row, domain) == dominant:
            concentration_streak += 1
        else:
            break
    branch_pressure = _clamp(
        0.28 * float(pressure_state.get("novelty_pressure", 0.0))
        + 0.28 * float(pressure_state.get("domain_shift_pressure", 0.0))
        + 0.24 * max(0.0, dominance_index - 0.45)
        + 0.20 * max(0.0, policy_stagnation)
    )
    branch_budget = max(0, min(3, int(round(4 * branch_pressure + (1 if concentration_streak >= 6 else 0)))))
    pool = [
        f"{domain}:root",
        f"{domain}:novelty",
        f"{domain}:repair",
        f"{domain}:domain_shift",
        f"{domain}:evaluation",
    ]
    active_pool = pool[: max(2, min(len(pool), 2 + branch_budget))]
    forced_branch = concentration_streak >= 8 or dominance_index >= 0.82
    selector = (int(tick) + int(round(10 * float(pressure_state.get("novelty_pressure", 0.0)))) + evaluation_generations) % len(active_pool)
    if forced_branch:
        selector = (selector + 1) % len(active_pool)
    selected_lineage = active_pool[selector]
    return {
        "selected_lineage": selected_lineage,
        "candidate_lineages": active_pool,
        "branch_rate": _clamp(branch_budget / 3.0),
        "merge_rate": _clamp(max(0.0, 0.24 - (branch_budget / 9.0))),
        "active_lineage_count": len(active_pool),
        "dormant_lineage_count": max(0, len(pool) - len(active_pool)),
        "branch_budget": branch_budget,
        "concentration_streak": concentration_streak,
        "forced_branch": forced_branch,
        "evaluation_branch_rate": _clamp((branch_budget / 3.0) * (0.5 + 0.5 * max(0.0, 1.0 - dominance_index))),
        "diversification_actions": [
            action
            for action in (
                "force_branching_pressure" if forced_branch else "",
                "force_evaluation_diversification" if forced_branch else "",
                "reduce_dominant_lineage_allocation" if dominance_index > 0.7 else "",
            )
            if action
        ],
        "dominance_index": round(dominance_index, 4),
    }


__all__ = ["lineage_branching"]
