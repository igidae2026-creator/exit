from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Iterable, Mapping


DEFAULT_EVENT_LOG = ".metaos_runtime/data/events.jsonl"
DEFAULT_METRICS_LOG = ".metaos_runtime/data/metrics.jsonl"
DEFAULT_ARTIFACT_LOG = ".metaos_runtime/data/artifact_registry.jsonl"


def _path(env_name: str, default: str) -> Path:
    path = Path(os.environ.get(env_name, default))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def event_log_path() -> Path:
    return _path("METAOS_EVENT_LOG", DEFAULT_EVENT_LOG)


def metrics_log_path() -> Path:
    return _path("METAOS_METRICS", DEFAULT_METRICS_LOG)


def artifact_log_path() -> Path:
    return _path("METAOS_REGISTRY", DEFAULT_ARTIFACT_LOG)


def append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(row), ensure_ascii=True) + "\n")


def append_event(event_type: str, payload: Mapping[str, Any]) -> None:
    append_jsonl(event_log_path(), {"t": time.time(), "type": event_type, "payload": dict(payload)})


def append_metrics(payload: Mapping[str, Any]) -> None:
    append_jsonl(metrics_log_path(), dict(payload))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def read_events() -> list[dict[str, Any]]:
    return read_jsonl(event_log_path())


def read_metrics() -> list[dict[str, Any]]:
    return read_jsonl(metrics_log_path())


def read_artifact_log() -> list[dict[str, Any]]:
    return read_jsonl(artifact_log_path())

