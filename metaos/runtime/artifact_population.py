from __future__ import annotations

from typing import Any, Mapping, Sequence


_TRACKED_CLASSES = (
    "strategy",
    "policy",
    "evaluation",
    "strategy_of_strategy",
    "domain",
    "repair",
)


def artifact_population(history: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(history or [])[-48:]
    previous = rows[:-12] if len(rows) > 12 else rows[:-1]
    recent = rows[-12:] if len(rows) >= 12 else rows
    population_counts = {name: 0 for name in _TRACKED_CLASSES}
    previous_counts = {name: 0 for name in _TRACKED_CLASSES}

    for row in recent:
        selection = row.get("civilization_selection", {}) if isinstance(row.get("civilization_selection"), Mapping) else {}
        selected = str(selection.get("selected_artifact_type", ""))
        if selected in population_counts:
            population_counts[selected] += 1

    for row in previous:
        selection = row.get("civilization_selection", {}) if isinstance(row.get("civilization_selection"), Mapping) else {}
        selected = str(selection.get("selected_artifact_type", ""))
        if selected in previous_counts:
            previous_counts[selected] += 1

    window = max(1, len(recent))
    prior_window = max(1, len(previous))
    growth_rates = {
        name: round((population_counts[name] / window) - (previous_counts[name] / prior_window), 4)
        for name in _TRACKED_CLASSES
    }
    extinction_risk = {
        name: round(max(0.0, 1.0 - (population_counts[name] / max(1, len(recent) * 0.2))), 4)
        for name in _TRACKED_CLASSES
    }
    return {
        "population_counts": population_counts,
        "growth_rates": growth_rates,
        "extinction_risk": extinction_risk,
    }

