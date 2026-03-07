from __future__ import annotations

from typing import Any, Mapping, Sequence


def civilization_governor(
    history: Sequence[Mapping[str, Any]],
    ecology: Mapping[str, float],
    market: Mapping[str, float],
) -> dict[str, Any]:
    rows = history[-24:] if history else ()
    ecology = dict(ecology or {})
    market = dict(market or {})
    counts: dict[str, int] = {}
    total = 0
    for row in rows:
        selection = row.get("civilization_selection", {}) if isinstance(row.get("civilization_selection"), Mapping) else {}
        selected = str(selection.get("selected_artifact_type", ""))
        if not selected:
            continue
        counts[selected] = counts.get(selected, 0) + 1
        total += 1
    dominant_share = (max(counts.values()) / total) if total else 0.0
    population_pressure = round(max(0.0, dominant_share - 0.45), 4)
    artifact_overproduction = round(max(0.0, dominant_share - 0.60), 4)
    ecosystem_balance = round(
        max(
            0.0,
            min(
                1.0,
                (
                    float(ecology.get("novelty_health", 0.5))
                    + float(ecology.get("diversity_health", 0.5))
                    + float(ecology.get("efficiency_health", 0.5))
                    + float(ecology.get("repair_health", 0.5))
                )
                / 4.0,
            ),
        ),
        4,
    )
    selection_drift = round(
        max(0.0, dominant_share - float(ecology.get("diversity_health", 0.5)) * 0.5 - float(market.get("selection_bias", 0.0)) * 0.2),
        4,
    )
    intervention = artifact_overproduction > 0.0 or selection_drift > 0.18 or ecosystem_balance < 0.55
    actions: list[str] = []
    if artifact_overproduction > 0.0:
        actions.append("rebalance_resource_allocation")
    if selection_drift > 0.18:
        actions.append("increase_diversity_pressure")
    if ecosystem_balance < 0.55:
        actions.append("spawn_exploration_quest")
    return {
        "population_pressure": population_pressure,
        "artifact_overproduction": artifact_overproduction,
        "ecosystem_balance": ecosystem_balance,
        "selection_drift": selection_drift,
        "intervention": intervention,
        "actions": actions,
    }
