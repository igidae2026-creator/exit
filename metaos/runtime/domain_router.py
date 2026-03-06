from __future__ import annotations

from typing import Any, Mapping

from metaos.runtime.domain_pool import list_domains


def route(
    pressure: Mapping[str, float],
    budgets: Mapping[str, float],
    *,
    domain: str = "default",
    guard: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    guard = dict(guard or {})
    domains = list_domains()
    if len(domains) <= 1 and domain in domains:
        weight = 1.0 + float(pressure.get("domain_shift_pressure", 0.0)) + (float(budgets.get("domain_budget", 0.0)) / 100.0)
        routing_weights = {domain: round(weight, 6)}
        return {"selected_domain": domain, "routing_weights": routing_weights}

    base_weight = 1.0 + float(pressure.get("domain_shift_pressure", 0.0)) + (float(budgets.get("domain_budget", 0.0)) / 100.0)
    routing_weights: dict[str, float] = {}
    for name in domains:
        weight = base_weight if name == domain else max(0.85, base_weight - 0.12)
        if guard.get("routing_stagnation") or guard.get("force_reframing"):
            weight += 0.08 if name != domain else -0.04
        routing_weights[name] = round(weight, 6)
    selected_domain = max(routing_weights, key=routing_weights.get)
    return {"selected_domain": selected_domain, "routing_weights": routing_weights}
