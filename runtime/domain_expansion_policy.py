from __future__ import annotations

from typing import Any, Mapping, Sequence


def _float(mapping: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(mapping.get(key, default))
    except Exception:
        return default


def domain_expansion_policy(
    pressure: Mapping[str, Any],
    civilization_memory: Mapping[str, Any],
    topology: Mapping[str, Any] | None = None,
    *,
    recent_decisions: Sequence[Mapping[str, Any]] | None = None,
    max_new_domains_per_window: int = 3,
    minimum_evidence_threshold: float = 0.45,
    cooldown_between_domain_spawns: int = 3,
) -> dict[str, Any]:
    pressure_state = dict(pressure or {})
    memory_state = dict(civilization_memory or {})
    topology_state = dict(topology or {})
    recent = list(recent_decisions or [])
    novelty = _float(pressure_state, "novelty_pressure")
    diversity = _float(pressure_state, "diversity_pressure")
    domain_shift = _float(pressure_state, "domain_shift_pressure")
    knowledge_density = _float(memory_state, "knowledge_density")
    memory_growth = _float(memory_state, "memory_growth")
    domain_distribution = dict(memory_state.get("domain_distribution", {})) if isinstance(memory_state.get("domain_distribution"), Mapping) else {}
    active_domain_distribution = dict(memory_state.get("active_domain_distribution", {})) if isinstance(memory_state.get("active_domain_distribution"), Mapping) else {}
    inactive_domains = list(memory_state.get("inactive_domains", [])) if isinstance(memory_state.get("inactive_domains"), list) else []
    domain_count = max(int(memory_state.get("created_domain_count", len(domain_distribution)) or len(domain_distribution)), int(topology_state.get("domain_count", 0) or 0), 1)
    active_domain_count = max(int(memory_state.get("active_domain_count", len(active_domain_distribution)) or len(active_domain_distribution)), 1)
    expansion_budget = max(0, int(topology_state.get("domain_expansion_budget", 0) or 0))
    created_recently = sum(1 for row in recent if row.get("created"))
    cooldown_remaining = 0 if not recent else max(0, cooldown_between_domain_spawns - len(recent))
    evidence = round((0.35 * novelty) + (0.30 * domain_shift) + (0.20 * diversity) + (0.10 * knowledge_density) + (0.05 * memory_growth), 4)
    lifecycle_drag = 0.04 * max(0, domain_count - active_domain_count)
    expansion_pressure = round(max(0.0, evidence - (0.06 * max(0, active_domain_count - 2)) + (0.02 * len(inactive_domains)) - lifecycle_drag), 4)
    allow = (
        evidence >= minimum_evidence_threshold
        and expansion_budget > 0
        and created_recently < max_new_domains_per_window
        and cooldown_remaining == 0
        and active_domain_count >= max(1, domain_count // 3)
    )
    branch_opportunity_score = round(max(0.0, evidence + (0.08 * len(inactive_domains)) - lifecycle_drag), 4)
    target_domains = max(3, min(12, domain_count + max(1, expansion_budget)))
    incoming_scope = str(topology_state.get("domain_scope", "local"))
    federation_adopt = allow and incoming_scope in {"local", "shared"} and evidence >= minimum_evidence_threshold
    return {
        "expansion_pressure": expansion_pressure,
        "evidence": evidence,
        "allowed": allow,
        "target_domain_count": int(target_domains),
        "active_domain_count": int(active_domain_count),
        "inactive_domain_count": len(inactive_domains),
        "max_new_domains_per_window": int(max_new_domains_per_window),
        "minimum_evidence_threshold": float(minimum_evidence_threshold),
        "activation_evidence_threshold": float(minimum_evidence_threshold),
        "cooldown_between_domain_spawns": int(cooldown_between_domain_spawns),
        "cooldown_remaining": int(cooldown_remaining),
        "created_recently": int(created_recently),
        "bounded": True,
        "branch_opportunity_score": branch_opportunity_score,
        "domain_scope": incoming_scope,
        "federation_adopt": federation_adopt,
        "expansion_decisions": [
            {
                "allowed": allow,
                "federation_adopt": federation_adopt,
                "evidence": evidence,
                "domain_count": int(domain_count),
                "domain_expansion_budget": int(expansion_budget),
                "target_domain_count": int(target_domains),
                "cooldown_remaining": int(cooldown_remaining),
                "branch_opportunity_score": branch_opportunity_score,
            }
        ],
    }


__all__ = ["domain_expansion_policy"]
