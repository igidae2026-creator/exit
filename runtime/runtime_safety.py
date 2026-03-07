from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from genesis.replay import replay_state
from runtime.civilization_state import civilization_state
from runtime.pressure_derivation import pressure_frame
from runtime.self_tuning_guardrails import self_tuning_guardrails


def _path(env_name: str, root_name: str) -> Path:
    if os.environ.get(env_name):
        return Path(os.environ[env_name])
    root = Path(os.environ.get("METAOS_ROOT", ".metaos_runtime"))
    return root / root_name


def runtime_safety() -> dict[str, Any]:
    event_log = _path("METAOS_EVENT_LOG", "events.jsonl")
    metrics_log = _path("METAOS_METRICS", "metrics.jsonl")
    registry_log = _path("METAOS_REGISTRY", "artifact_registry.jsonl")
    archive_log = _path("METAOS_ARCHIVE", "archive/archive.jsonl")
    sizes = {
        "events": event_log.stat().st_size if event_log.exists() else 0,
        "metrics": metrics_log.stat().st_size if metrics_log.exists() else 0,
        "registry": registry_log.stat().st_size if registry_log.exists() else 0,
        "archive": archive_log.stat().st_size if archive_log.exists() else 0,
    }
    total = sum(sizes.values())
    storage_pressure = round(min(1.0, total / float(64 * 1024 * 1024)), 4)
    runtime_pressure = round(min(1.0, (sizes["events"] + sizes["metrics"]) / float(32 * 1024 * 1024)), 4)
    archive_pressure = round(min(1.0, (sizes["archive"] + sizes["registry"]) / float(32 * 1024 * 1024)), 4)
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
    guardrails = self_tuning_guardrails(
        civilization,
        {"economy_balance_score": float(civilization.get("economy_balance_score", 0.0))},
        {"stability_score": float(civilization.get("stability_score", 0.0)), "drift_score": float(civilization.get("drift_score", 0.0)), "stagnation_score": float(civilization.get("stagnation_score", 0.0)), "overexpansion_score": float(civilization.get("overexpansion_score", 0.0)), "underexploration_score": float(civilization.get("underexploration_score", 0.0))},
    )
    actions.extend(str(name) for name in guardrails.get("guardrail_actions", []) if str(name) not in actions)
    return {
        "storage_pressure": storage_pressure,
        "runtime_pressure": runtime_pressure,
        "archive_pressure": archive_pressure,
        "safety_actions": actions,
        "log_sizes": sizes,
        "replay_ok": bool(replay),
        "surviving_lineages": surviving_lineages,
        "active_domains": active_domains,
        "pressure": pressure,
        "guardrail_state": dict(guardrails.get("guardrail_state", {})),
        "tuned_thresholds": dict(guardrails.get("tuned_thresholds", {})),
        "guardrail_actions": list(guardrails.get("guardrail_actions", [])),
    }


__all__ = ["runtime_safety"]
