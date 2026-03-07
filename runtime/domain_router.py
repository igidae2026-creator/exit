from __future__ import annotations

from typing import Any, Mapping

from runtime.domain_pool import domain_names, domain_snapshot


def route(
    pressure: Mapping[str, float],
    budgets: Mapping[str, float],
    *,
    domain: str = "default",
    guard: Mapping[str, Any] | None = None,
    ecology: Mapping[str, float] | None = None,
    civilization_selection: Mapping[str, Any] | None = None,
    history: list[Mapping[str, Any]] | None = None,
) -> dict[str, object]:
    guard = dict(guard or {})
    ecology = dict(ecology or {})
    civilization_selection = dict(civilization_selection or {})
    snapshot = domain_snapshot()
    domains = list(snapshot.get("active_domains", [])) or domain_names()
    if len(domains) <= 1 and domain in domains:
        weight = 1.0 + float(pressure.get("domain_shift_pressure", 0.0)) + (float(budgets.get("domain_budget", 0.0)) / 100.0)
        routing_weights = {domain: round(weight, 6)}
        return {"selected_domain": domain, "routing_weights": routing_weights, "domain_pool": snapshot}

    base_weight = 1.0 + float(pressure.get("domain_shift_pressure", 0.0)) + (float(budgets.get("domain_budget", 0.0)) / 100.0)
    selected_type = str(civilization_selection.get("selected_artifact_type", "policy"))
    recent = [str((row.get("routing", {}) if isinstance(row.get("routing"), Mapping) else {}).get("selected_domain", "")) for row in list(history or [])[-8:]]
    routing_weights: dict[str, float] = {}
    for index, name in enumerate(domains):
        weight = base_weight if name == domain else max(0.82, base_weight - 0.1)
        if selected_type in {"policy", "evaluation", "allocator"}:
            weight += 0.08 if name == domain else -0.03
        if name != domain:
            weight += 0.08 * float(pressure.get("diversity_pressure", 0.0))
            weight += 0.06 * float(pressure.get("domain_shift_pressure", 0.0))
            weight += 0.05 * (1.0 - float(ecology.get("diversity_health", 0.5)))
            weight += 0.03 * (1.0 - float(ecology.get("exploration_health", 0.5)))
            weight += 0.02 * index
        if guard.get("routing_stagnation") or guard.get("force_reframing"):
            weight += 0.08 if name != domain else -0.04
        if recent and recent.count(name) == len(recent):
            weight += 0.08 if name != domain else -0.08
        if selected_type in {"domain", "strategy_of_strategy"} and name != domain:
            weight += 0.04
        if selected_type == "repair" and name == domain:
            weight += 0.04
        routing_weights[name] = round(weight, 6)
    selected_domain = max(routing_weights, key=routing_weights.get)
    return {"selected_domain": selected_domain, "routing_weights": routing_weights, "domain_pool": snapshot}
