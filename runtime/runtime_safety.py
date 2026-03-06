from __future__ import annotations

import os
from pathlib import Path
from typing import Any


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
    return {
        "storage_pressure": storage_pressure,
        "runtime_pressure": runtime_pressure,
        "archive_pressure": archive_pressure,
        "safety_actions": actions,
        "log_sizes": sizes,
    }


__all__ = ["runtime_safety"]
