from __future__ import annotations

from typing import Any, Mapping

from metaos.registry.artifact_registry import register


REPAIR_TYPES = {
    "retry_once",
    "quota_downshift",
    "export_freeze",
    "replay_restore",
}


def choose_repair(metrics: Mapping[str, float], pressure: Mapping[str, float]) -> str | None:
    repair_pressure = float(pressure.get("repair_pressure", 0.0))
    fail_rate = float(metrics.get("fail_rate", 0.0))
    cost = float(metrics.get("cost", 0.0))
    diversity_pressure = float(pressure.get("diversity_pressure", 0.0))

    if repair_pressure < 0.6 and fail_rate < 0.5:
        return None
    if fail_rate >= 0.8:
        return "replay_restore"
    if cost >= 0.7:
        return "quota_downshift"
    if diversity_pressure >= 0.85:
        return "export_freeze"
    return "retry_once"


def emit_repair_artifact(
    metrics: Mapping[str, float],
    pressure: Mapping[str, float],
    *,
    parent: str | None = None,
) -> dict[str, Any] | None:
    repair_type = choose_repair(metrics, pressure)
    if repair_type is None:
        return None
    artifact_id = register(
        data={"metrics": dict(metrics), "pressure": dict(pressure), "action": repair_type},
        parent=parent,
        atype="repair",
        score=float(metrics.get("score", 0.0)),
        novelty=float(metrics.get("novelty", 0.0)),
        diversity=float(metrics.get("diversity", 0.0)),
        cost=float(metrics.get("cost", 0.0)),
    )
    return {"artifact_id": artifact_id, "type": repair_type}
