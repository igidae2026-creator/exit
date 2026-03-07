from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, float(value))), 4)


def _domain_from_row(row: Mapping[str, Any]) -> str:
    routing = row.get("routing", {}) if isinstance(row.get("routing"), Mapping) else {}
    return str(routing.get("selected_domain") or row.get("domain") or "").strip()


def domain_lifecycle_state(
    civilization: Mapping[str, Any],
    *,
    history: Sequence[Mapping[str, Any]] | None = None,
    pressure_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    civilization_state = dict(civilization or {})
    rows = list(history or [])
    pressure = dict(pressure_state or {})
    created_domains = sorted(str(name) for name in civilization_state.get("created_domains", []) if str(name))
    active_domains = sorted(str(name) for name in civilization_state.get("active_domains", []) if str(name))
    inactive_domains = sorted(str(name) for name in civilization_state.get("inactive_domains", []) if str(name))
    recent_counts: Counter[str] = Counter()
    long_counts: Counter[str] = Counter()
    for row in rows[-32:]:
        name = _domain_from_row(row)
        if name:
            recent_counts[name] += 1
    for row in rows[-128:]:
        name = _domain_from_row(row)
        if name:
            long_counts[name] += 1
    known = sorted(set(created_domains) | set(active_domains) | set(inactive_domains) | set(recent_counts) | set(long_counts))
    imported_domains = int(civilization_state.get("imported_domains", 0) or 0)
    adopted_domains = int(civilization_state.get("adopted_domains", 0) or 0)
    active_imported_domains = int(civilization_state.get("active_imported_domains", 0) or 0)
    active = sorted(name for name in known if recent_counts.get(name, 0) > 0 or name in set(active_domains))
    inactive = sorted(name for name in known if name not in set(active) and (long_counts.get(name, 0) > 0 or name in set(inactive_domains)))
    retired = sorted(name for name in inactive if long_counts.get(name, 0) <= 1 and recent_counts.get(name, 0) == 0)
    resurrection_pressure = (
        0.45 * float(pressure.get("domain_shift_pressure", 0.0))
        + 0.35 * float(pressure.get("diversity_pressure", 0.0))
        + 0.20 * float(pressure.get("novelty_pressure", 0.0))
    )
    resurrectable = sorted(name for name in retired if resurrection_pressure >= 0.55)
    lineage_domain_matrix: dict[str, list[str]] = {}
    domain_lineage_total = 0
    for row in rows[-128:]:
        name = _domain_from_row(row)
        lineage = str(
            ((row.get("lineage") or {}) if isinstance(row.get("lineage"), Mapping) else {}).get("selected_lineage")
            or ((row.get("routing") or {}) if isinstance(row.get("routing"), Mapping) else {}).get("selected_lineage")
            or ""
        )
        if name and lineage:
            lineage_domain_matrix.setdefault(name, [])
            if lineage not in lineage_domain_matrix[name]:
                lineage_domain_matrix[name].append(lineage)
                domain_lineage_total += 1
    active_rate = _clamp(len(active) / max(1.0, float(len(known))))
    retirement_rate = _clamp(len(retired) / max(1.0, float(len(known))))
    turnover = _clamp((len(active) + len(retired)) / max(1.0, float((2 * len(known)) or 1)))
    transitions: list[str] = []
    if retirement_rate > 0.45:
        transitions.append("slow_domain_creation")
    if resurrection_pressure >= 0.55 and resurrectable:
        transitions.append("allow_domain_resurrection")
    if active_rate < 0.34 and inactive:
        transitions.append("reactivate_evidenced_domain")
    return {
        "created_domains": known,
        "active_domains": active,
        "inactive_domains": inactive,
        "retired_domains": retired,
        "resurrectable_domains": resurrectable,
        "resurrectable_domain_count": len(resurrectable),
        "domain_turnover": turnover,
        "domain_activation_rate": active_rate,
        "domain_retirement_rate": retirement_rate,
        "lineage_domain_matrix": lineage_domain_matrix,
        "domain_lineage_coverage": round(domain_lineage_total / max(1.0, float(len(known) or 1)), 4),
        "dormant_domain_reactivation_count": len(resurrectable),
        "imported_domains": imported_domains,
        "adopted_domains": adopted_domains,
        "active_imported_domains": active_imported_domains,
        "domain_origin_node": str(civilization_state.get("domain_origin_node", "")),
        "domain_adoption_history": list(civilization_state.get("domain_adoption_history", [])) if isinstance(civilization_state.get("domain_adoption_history"), list) else [],
        "lifecycle_actions": transitions,
        "bounded": True,
    }


__all__ = ["domain_lifecycle_state"]
