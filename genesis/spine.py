from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterator, Mapping


DEFAULT_ROOT = ".metaos_runtime/data"
DEFAULT_EVENT_LOG = "events.jsonl"
DEFAULT_METRICS_LOG = "metrics.jsonl"
DEFAULT_ARTIFACT_LOG = "artifact_registry.jsonl"


def _root() -> Path:
    return Path(os.environ.get("METAOS_ROOT", DEFAULT_ROOT))


def _path(env_name: str, filename: str) -> Path:
    explicit = os.environ.get(env_name)
    path = Path(explicit) if explicit else _root() / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def event_log_path() -> Path:
    return _path("METAOS_EVENT_LOG", DEFAULT_EVENT_LOG)


def metrics_log_path() -> Path:
    return _path("METAOS_METRICS", DEFAULT_METRICS_LOG)


def artifact_log_path() -> Path:
    return _path("METAOS_REGISTRY", DEFAULT_ARTIFACT_LOG)


def _append(path: Path, row: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    data = json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + "\n"
    fd = os.open(str(path), os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    try:
        os.write(fd, data.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    return payload


def append_jsonl(path: Path, row: Mapping[str, Any]) -> dict[str, Any]:
    return _append(path, row)


def append_event(event_type: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    return _append(event_log_path(), {"event_type": str(event_type), "payload": dict(payload)})


def append_metrics(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _append(metrics_log_path(), dict(payload))


def append_artifact_registry(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _append(artifact_log_path(), dict(payload))


def _read(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return _read(path)


def read_events() -> list[dict[str, Any]]:
    return _read(event_log_path())


def read_metrics() -> list[dict[str, Any]]:
    return _read(metrics_log_path())


def read_artifact_log() -> list[dict[str, Any]]:
    return _read(artifact_log_path())


def iter_truth_paths() -> Iterator[Path]:
    for path in (event_log_path(), metrics_log_path(), artifact_log_path()):
        yield path


__all__ = [
    "append_artifact_registry",
    "append_event",
    "append_jsonl",
    "append_metrics",
    "artifact_log_path",
    "event_log_path",
    "iter_truth_paths",
    "metrics_log_path",
    "read_artifact_log",
    "read_events",
    "read_jsonl",
    "read_metrics",
]
