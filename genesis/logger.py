from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator

from validation.immutability import assert_writable

EVENTS_LOG = "events.jsonl"
STRATEGIES_LOG = "strategies.jsonl"
METRICS_LOG = "metrics.jsonl"
ARTIFACT_REGISTRY_LOG = "artifact_registry.jsonl"


@dataclass(frozen=True)
class LogRecord:
    timestamp: str
    event_type: str
    payload: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return {"timestamp": self.timestamp, "event_type": self.event_type, "payload": self.payload}


class AppendOnlyLogger:
    def __init__(self, log_dir: str | Path = ".") -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_event(self, event_type: str, payload: Dict[str, Any]) -> LogRecord:
        return self._append(EVENTS_LOG, event_type, payload)

    def log_strategy(self, event_type: str, payload: Dict[str, Any]) -> LogRecord:
        return self._append(STRATEGIES_LOG, event_type, payload)

    def log_metric(self, event_type: str, payload: Dict[str, Any]) -> LogRecord:
        return self._append(METRICS_LOG, event_type, payload)

    def log_artifact_registry(self, event_type: str, payload: Dict[str, Any]) -> LogRecord:
        return self._append(ARTIFACT_REGISTRY_LOG, event_type, payload)

    def replay_events(self) -> Iterator[LogRecord]:
        return self._replay(EVENTS_LOG)

    def replay_metrics(self) -> Iterator[LogRecord]:
        return self._replay(METRICS_LOG)

    def replay_artifact_registry(self) -> Iterator[LogRecord]:
        return self._replay(ARTIFACT_REGISTRY_LOG)

    def replay_file(self, filename: str) -> Iterator[LogRecord]:
        return self._replay(filename)

    def _append(self, filename: str, event_type: str, payload: Dict[str, Any]) -> LogRecord:
        if not event_type or not isinstance(event_type, str):
            raise ValueError("event_type must be a non-empty string")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict")
        record = LogRecord(datetime.now(timezone.utc).isoformat(), event_type, dict(payload))
        path = self.log_dir / filename
        assert_writable([path])
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
        try:
            os.write(fd, (json.dumps(record.as_dict(), ensure_ascii=True, separators=(",", ":")) + "\n").encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)
        return record

    def _replay(self, filename: str) -> Iterator[LogRecord]:
        path = self.log_dir / filename
        if not path.exists():
            return iter(())

        def _iter() -> Iterator[LogRecord]:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        continue
                    timestamp = row.get("timestamp")
                    event_type = row.get("event_type")
                    payload = row.get("payload")
                    if isinstance(timestamp, str) and isinstance(event_type, str) and isinstance(payload, dict):
                        yield LogRecord(timestamp, event_type, payload)

        return _iter()


def log_event(event_type: str, payload: Dict[str, Any], *, data_dir: str | Path = "data") -> Dict[str, Any]:
    return AppendOnlyLogger(log_dir=data_dir).log_event(event_type, payload).as_dict()


def log_metric(payload: Dict[str, Any], *, data_dir: str | Path = "data") -> Dict[str, Any]:
    return AppendOnlyLogger(log_dir=data_dir).log_metric("metrics", payload).as_dict()


def log_artifact_registry(payload: Dict[str, Any], *, data_dir: str | Path = "data") -> Dict[str, Any]:
    return AppendOnlyLogger(log_dir=data_dir).log_artifact_registry("artifact_registered", payload).as_dict()


def replay_log(filename: str, log_dir: str | Path = ".") -> Iterable[LogRecord]:
    logger = AppendOnlyLogger(log_dir=log_dir)
    return logger.replay_file(filename)


__all__ = [
    "ARTIFACT_REGISTRY_LOG",
    "AppendOnlyLogger",
    "EVENTS_LOG",
    "LogRecord",
    "METRICS_LOG",
    "STRATEGIES_LOG",
    "log_artifact_registry",
    "log_event",
    "log_metric",
    "replay_log",
]
