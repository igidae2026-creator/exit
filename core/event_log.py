from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

from core.constitution_guard import assert_writable


@dataclass(slots=True, frozen=True)
class SpinePaths:
    root: Path
    events_path: Path
    registry_path: Path
    metrics_path: Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_spine(data_dir: str | Path = "data") -> SpinePaths:
    root = Path(data_dir)
    return SpinePaths(
        root=root,
        events_path=root / "events.jsonl",
        registry_path=root / "artifact_registry.jsonl",
        metrics_path=root / "metrics.jsonl",
    )


def ensure_spine(data_dir: str | Path = "data") -> SpinePaths:
    spine = resolve_spine(data_dir)
    spine.root.mkdir(parents=True, exist_ok=True)
    for path in (spine.events_path, spine.registry_path, spine.metrics_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
    return spine


def append_jsonl(path: str | Path, record: Mapping[str, Any]) -> None:
    target = Path(path)
    assert_writable([target])
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(dict(record), ensure_ascii=True, separators=(",", ":")) + "\n"
    fd = os.open(str(target), os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    try:
        os.write(fd, payload.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)


def read_jsonl(path: str | Path) -> Iterator[dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return
    with target.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                yield row


def append_event(event_type: str, payload: Mapping[str, Any], data_dir: str | Path = "data") -> dict[str, Any]:
    spine = ensure_spine(data_dir)
    row = {
        "timestamp": utc_now(),
        "event_type": event_type,
        "payload": dict(payload),
    }
    append_jsonl(spine.events_path, row)
    return row


def append_metric(payload: Mapping[str, Any], data_dir: str | Path = "data") -> dict[str, Any]:
    spine = ensure_spine(data_dir)
    row = {
        "timestamp": utc_now(),
        "event_type": "metrics",
        "payload": dict(payload),
    }
    append_jsonl(spine.metrics_path, row)
    return row


def read_events(data_dir: str | Path = "data") -> Iterable[dict[str, Any]]:
    return read_jsonl(resolve_spine(data_dir).events_path)


def read_registry(data_dir: str | Path = "data") -> Iterable[dict[str, Any]]:
    return read_jsonl(resolve_spine(data_dir).registry_path)


def read_metrics(data_dir: str | Path = "data") -> Iterable[dict[str, Any]]:
    return read_jsonl(resolve_spine(data_dir).metrics_path)
