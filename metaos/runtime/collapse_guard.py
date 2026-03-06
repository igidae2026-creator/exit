from __future__ import annotations

from typing import Any, Mapping, Sequence


def _avg(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _history_value(row: Mapping[str, Any], key: str, nested: str | None = None) -> float:
    if key in row:
        return float(row.get(key, 0.0))
    if nested and isinstance(row.get(nested), Mapping):
        return float(row[nested].get(key, 0.0))
    return 0.0


def detect_guard_state(history: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(history)[-20:]
    novelty = [_history_value(row, "novelty") for row in rows]
    fail_rate = [_history_value(row, "fail_rate") for row in rows]
    lineage = [_history_value(row, "lineage_pressure", "pressure") for row in rows]
    domain_shift = [_history_value(row, "domain_shift_pressure", "pressure") for row in rows]
    worker_budgets = [_history_value(row, "effective_workers", "budgets") for row in rows]
    total_budgets = []
    selected_domains: list[str] = []
    repairs = 0

    for row in rows:
        budgets = row.get("budgets", {}) if isinstance(row.get("budgets"), Mapping) else {}
        total_budgets.append(
            sum(float(budgets.get(key, 0.0)) for key in ("mutation_budget", "replay_budget", "repair_budget", "archive_budget", "domain_budget"))
        )
        routing = row.get("routing", {}) if isinstance(row.get("routing"), Mapping) else {}
        selected_domains.append(str(routing.get("selected_domain", row.get("domain", "default"))))
        if row.get("repair"):
            repairs += 1

    lineage_collapse = _avg(lineage) >= 0.75
    novelty_collapse = rows and _avg(novelty) <= 0.16
    repair_storm = repairs >= max(3, len(rows) // 3) or _avg(fail_rate) >= 0.32
    budget_inflation = bool(rows) and _avg(total_budgets) > max(10.0, _avg(worker_budgets) * 28.0)
    routing_stagnation = len(set(selected_domains[-8:])) <= 1 and _avg(domain_shift[-8:]) >= 0.45 if rows else False

    return {
        "lineage_collapse": lineage_collapse,
        "novelty_collapse": novelty_collapse,
        "repair_storm": repair_storm,
        "budget_inflation": budget_inflation,
        "routing_stagnation": routing_stagnation,
        "freeze_export": lineage_collapse or repair_storm,
        "downshift_workers": repair_storm or budget_inflation,
        "force_reframing": novelty_collapse or routing_stagnation,
        "force_meta": lineage_collapse or routing_stagnation,
        "reset_mutation_bias": novelty_collapse or repair_storm,
    }
