from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ecosystem.ecosystem_state import ecosystem_state
from federation.federation_state import federation_state
from genesis.replay import replay_state
from runtime.civilization_state import civilization_state
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
    surviving_lineages = len(dict(civilization.get("lineage_counts", {})))
    active_domains = len(dict(civilization.get("domain_distribution", {})))
    if surviving_lineages <= 1:
        actions.append("force_diversity_recovery")
    if active_domains <= 1:
        actions.append("force_domain_expansion_review")
    if float(pressure.get("repair_pressure", 0.0)) >= 0.75:
        actions.append("repair_escalation")
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
        civilization,
        {"economy_balance_score": float(civilization.get("economy_balance_score", 0.0))},
        {"stability_score": float(civilization.get("stability_score", 0.0)), "drift_score": float(civilization.get("drift_score", 0.0)), "stagnation_score": float(civilization.get("stagnation_score", 0.0)), "overexpansion_score": float(civilization.get("overexpansion_score", 0.0)), "underexploration_score": float(civilization.get("underexploration_score", 0.0))},
    )
    actions.extend(str(name) for name in guardrails.get("guardrail_actions", []) if str(name) not in actions)
    return {
        "profile": profile_spec.name,
        "storage_pressure": storage_pressure,
        "runtime_pressure": runtime_pressure,
        "archive_pressure": archive_pressure,
        "safety_actions": actions,
        "log_sizes": sizes,
        "replay_ok": bool(replay),
        "surviving_lineages": surviving_lineages,
        "active_domains": active_domains,
        "federation_nodes": federation_nodes,
        "ecosystem_nodes": node_population,
        "artifact_exchange_rate": artifact_exchange_rate,
        "domain_propagation_rate": domain_propagation_rate,
        "pressure": pressure,
        "guardrail_state": dict(guardrails.get("guardrail_state", {})),
        "tuned_thresholds": dict(guardrails.get("tuned_thresholds", {})),
        "guardrail_actions": list(guardrails.get("guardrail_actions", [])),
    }


__all__ = ["runtime_safety"]
