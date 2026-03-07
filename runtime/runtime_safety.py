from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ecosystem.ecosystem_state import ecosystem_state
from federation.federation_state import federation_state
from genesis.replay import replay_state
from runtime.civilization_state import civilization_state
from runtime.genesis_ceiling import (
    DOMAIN_ECOLOGY,
    DOMINANCE_CAP,
    DOMINANCE_EMERGENCY,
    LINEAGE_ECOLOGY,
    failure_protocol_state,
)
from runtime.pressure_derivation import pressure_frame
from runtime.profiles import runtime_profile
from runtime.self_tuning_guardrails import self_tuning_guardrails


def _path(env_name: str, root_name: str) -> Path:
    if os.environ.get(env_name):
        return Path(os.environ[env_name])
    root = Path(os.environ.get("METAOS_ROOT", ".metaos_runtime"))
    return root / root_name


def runtime_safety(*, profile: str | None = None) -> dict[str, Any]:
    event_log = _path("METAOS_EVENT_LOG", "events.jsonl")
    metrics_log = _path("METAOS_METRICS", "metrics.jsonl")
    registry_log = _path("METAOS_REGISTRY", "artifact_registry.jsonl")
    archive_log = _path("METAOS_ARCHIVE", "archive/archive.jsonl")
    profile_spec = runtime_profile(profile)
    sizes = {
        "events": event_log.stat().st_size if event_log.exists() else 0,
        "metrics": metrics_log.stat().st_size if metrics_log.exists() else 0,
        "registry": registry_log.stat().st_size if registry_log.exists() else 0,
        "archive": archive_log.stat().st_size if archive_log.exists() else 0,
    }
    total = sum(sizes.values())
    storage_pressure = round(min(1.0, total / float(profile_spec.storage_budget_bytes)), 4)
    runtime_pressure = round(min(1.0, (sizes["events"] + sizes["metrics"]) / float(profile_spec.runtime_budget_bytes)), 4)
    archive_pressure = round(min(1.0, (sizes["archive"] + sizes["registry"]) / float(profile_spec.archive_budget_bytes)), 4)
    actions: list[str] = []
    if storage_pressure > 0.5:
        actions.append("rotate_runtime")
    if archive_pressure > 0.5:
        actions.append("archive_pressure_review")
    if runtime_pressure > 0.5:
        actions.append("cleanup_runtime")
    replay = replay_state()
    civilization = civilization_state()
    pressure = pressure_frame(civilization)
    active_lineage_count = civilization.get("active_lineage_count")
    surviving_lineages = int(active_lineage_count) if active_lineage_count is not None else len(dict(civilization.get("lineage_counts", {})))
    active_domain_count = civilization.get("active_domain_count")
    active_domains = int(active_domain_count) if active_domain_count is not None else len(dict(civilization.get("active_domain_distribution", {})))
    dominance_index = float(civilization.get("dominance_index", 0.0) or 0.0)
    if surviving_lineages < LINEAGE_ECOLOGY.minimum:
        actions.append("force_diversity_recovery")
    if active_domains < DOMAIN_ECOLOGY.minimum:
        actions.append("force_domain_expansion_review")
    if float(pressure.get("repair_pressure", 0.0)) >= 0.75:
        actions.append("repair_escalation")
    if dominance_index > DOMINANCE_EMERGENCY:
        actions.append("anti_monoculture_repair")
        actions.append("resurrect_dormant_lineages")
    elif dominance_index > DOMINANCE_CAP:
        actions.append("dominance_watch")
    federation = federation_state()
    federation_nodes = len(list(federation.get("federation_nodes", [])))
    artifact_exchange_rate = float(federation.get("artifact_exchange_rate", 0.0) or 0.0)
    domain_propagation_rate = float(federation.get("domain_propagation_rate", 0.0) or 0.0)
    knowledge_events = int((federation.get("knowledge_propagation", {}) if isinstance(federation.get("knowledge_propagation"), dict) else {}).get("events", 0))
    if federation_nodes > max(8, profile_spec.worker_min // 4):
        actions.append("federation_overload")
    if artifact_exchange_rate > 0.75:
        actions.append("artifact_flood")
    if domain_propagation_rate > 0.5:
        actions.append("domain_explosion")
    if knowledge_events > max(512, profile_spec.worker_max):
        actions.append("policy_cascade")
        actions.append("knowledge_storm")
    if float(federation.get("hydration_rate", 0.0)) > 0.85:
        actions.append("mirror_storm")
    if float(federation.get("federation_monoculture_score", 0.0)) > 0.78:
        actions.append("foreign_monoculture")
    ecosystem = ecosystem_state()
    node_population = len(list(ecosystem.get("active_nodes", [])))
    cluster_count = len(dict(ecosystem.get("domain_clusters", {})))
    artifact_market = dict(ecosystem.get("artifact_market", {}))
    if node_population > 0 and cluster_count <= 1 and node_population > 3:
        actions.append("ecosystem_fragmentation")
    if sum(dict(artifact_market.get("artifact_supply", {})).values()) > max(64, profile_spec.worker_max):
        actions.append("ecosystem_artifact_flood")
    if cluster_count == 0 and node_population > 0:
        actions.append("domain_collapse")
    guardrails = self_tuning_guardrails(
        {
            **civilization,
            "artifact_exchange_rate": artifact_exchange_rate,
            "domain_propagation_rate": domain_propagation_rate,
            "policy_diffusion_rate": float(federation.get("policy_diffusion_rate", 0.0)),
            "knowledge_flow_rate": float(federation.get("knowledge_flow_rate", 0.0)),
            "hydration_rate": float(federation.get("hydration_rate", 0.0)),
            "mirror_lineage_count": int(federation.get("mirror_lineage_count", 0)),
            "federation_monoculture_score": float(federation.get("federation_monoculture_score", 0.0)),
        },
        {"economy_balance_score": float(civilization.get("economy_balance_score", 0.0))},
        {"stability_score": float(civilization.get("stability_score", 0.0)), "drift_score": float(civilization.get("drift_score", 0.0)), "stagnation_score": float(civilization.get("stagnation_score", 0.0)), "overexpansion_score": float(civilization.get("overexpansion_score", 0.0)), "underexploration_score": float(civilization.get("underexploration_score", 0.0))},
    )
    actions.extend(str(name) for name in guardrails.get("guardrail_actions", []) if str(name) not in actions)
    actions.extend(str(name) for name in guardrails.get("federation_safety_actions", []) if str(name) not in actions)
    replay_ok = bool(replay)
    protocol_state = failure_protocol_state(
        replay_ok=replay_ok,
        repair_pressure=float(pressure.get("repair_pressure", 0.0)),
        surviving_lineages=surviving_lineages,
        active_domains=active_domains,
        dominance_index=dominance_index,
    )
    return {
        "profile": profile_spec.name,
        "storage_pressure": storage_pressure,
        "runtime_pressure": runtime_pressure,
        "archive_pressure": archive_pressure,
        "safety_actions": actions,
        "log_sizes": sizes,
        "replay_ok": replay_ok,
        "surviving_lineages": surviving_lineages,
        "active_domains": active_domains,
        "lineage_floor": LINEAGE_ECOLOGY.minimum,
        "lineage_preferred_floor": LINEAGE_ECOLOGY.preferred,
        "domain_floor": DOMAIN_ECOLOGY.minimum,
        "domain_target_floor": DOMAIN_ECOLOGY.preferred,
        "lineage_floor_ok": surviving_lineages >= LINEAGE_ECOLOGY.minimum,
        "domain_floor_ok": active_domains >= DOMAIN_ECOLOGY.minimum,
        "dominance_index": dominance_index,
        "dominance_cap": DOMINANCE_CAP,
        "dominance_emergency_threshold": DOMINANCE_EMERGENCY,
        "dominance_state": (
            "emergency" if dominance_index > DOMINANCE_EMERGENCY else "watch" if dominance_index > DOMINANCE_CAP else "healthy"
        ),
        "failure_protocol_state": protocol_state,
        "federation_nodes": federation_nodes,
        "ecosystem_nodes": node_population,
        "federation_pressure": float(guardrails.get("federation_pressure", 0.0)),
        "federation_overload_score": float(guardrails.get("federation_overload_score", 0.0)),
        "federation_safety_actions": list(guardrails.get("federation_safety_actions", [])),
        "artifact_exchange_rate": artifact_exchange_rate,
        "domain_propagation_rate": domain_propagation_rate,
        "policy_diffusion_rate": float(federation.get("policy_diffusion_rate", 0.0)),
        "knowledge_flow_rate": float(federation.get("knowledge_flow_rate", 0.0)),
        "hydration_rate": float(federation.get("hydration_rate", 0.0)),
        "mirror_lineage_count": int(federation.get("mirror_lineage_count", 0)),
        "federation_monoculture_score": float(federation.get("federation_monoculture_score", 0.0)),
        "pressure": pressure,
        "guardrail_state": dict(guardrails.get("guardrail_state", {})),
        "tuned_thresholds": dict(guardrails.get("tuned_thresholds", {})),
        "guardrail_actions": list(guardrails.get("guardrail_actions", [])),
    }


__all__ = ["runtime_safety"]
