from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator


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
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "payload": self.payload,
        }


class AppendOnlyLogger:
    """Append-only JSONL logger with replay support."""

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

    def append(self, filename: str, event_type: str, payload: Dict[str, Any]) -> LogRecord:
        return self._append(filename, event_type, payload)

    def replay_events(self) -> Iterator[LogRecord]:
        return self._replay(EVENTS_LOG)

    def replay_strategies(self) -> Iterator[LogRecord]:
        return self._replay(STRATEGIES_LOG)

    def replay_metrics(self) -> Iterator[LogRecord]:
        return self._replay(METRICS_LOG)

    def replay_artifact_registry(self) -> Iterator[LogRecord]:
        return self._replay(ARTIFACT_REGISTRY_LOG)

    def replay_file(self, filename: str) -> Iterator[LogRecord]:
        return self._replay(filename)

    def _append(self, filename: str, event_type: str, payload: Dict[str, Any]) -> LogRecord:
        if not isinstance(filename, str) or not filename:
            raise ValueError("filename must be a non-empty string")
        if not isinstance(event_type, str) or not event_type:
            raise ValueError("event_type must be a non-empty string")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict")

        record = LogRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            payload=payload,
        )
        data = (json.dumps(record.as_dict(), separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")

        path = self.log_dir / filename
        fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
        try:
            os.write(fd, data)
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
                for line_number, line in enumerate(handle, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"invalid JSON in {path} at line {line_number}") from exc

                    if not isinstance(obj, dict):
                        raise ValueError(f"invalid record in {path} at line {line_number}: expected object")

                    timestamp = obj.get("timestamp")
                    event_type = obj.get("event_type")
                    payload = obj.get("payload")

                    if not isinstance(timestamp, str):
                        raise ValueError(f"invalid timestamp in {path} at line {line_number}")
                    if not isinstance(event_type, str):
                        raise ValueError(f"invalid event_type in {path} at line {line_number}")
                    if not isinstance(payload, dict):
                        raise ValueError(f"invalid payload in {path} at line {line_number}")

                    yield LogRecord(timestamp=timestamp, event_type=event_type, payload=payload)

        return _iter()


def append_event(event_type: str, payload: Dict[str, Any], log_dir: str | Path = ".") -> LogRecord:
    return AppendOnlyLogger(log_dir=log_dir).log_event(event_type, payload)


def append_strategy(event_type: str, payload: Dict[str, Any], log_dir: str | Path = ".") -> LogRecord:
    return AppendOnlyLogger(log_dir=log_dir).log_strategy(event_type, payload)


def append_metric(event_type: str, payload: Dict[str, Any], log_dir: str | Path = ".") -> LogRecord:
    return AppendOnlyLogger(log_dir=log_dir).log_metric(event_type, payload)


def replay_log(filename: str, log_dir: str | Path = ".") -> Iterable[LogRecord]:
    logger = AppendOnlyLogger(log_dir=log_dir)
    if filename == EVENTS_LOG:
        return logger.replay_events()
    if filename == STRATEGIES_LOG:
        return logger.replay_strategies()
    if filename == METRICS_LOG:
        return logger.replay_metrics()
    if filename == ARTIFACT_REGISTRY_LOG:
        return logger.replay_artifact_registry()
    return logger.replay_file(filename)


__all__ = [
    "ARTIFACT_REGISTRY_LOG",
    "EVENTS_LOG",
    "METRICS_LOG",
    "STRATEGIES_LOG",
    "AppendOnlyLogger",
    "LogRecord",
    "append_event",
    "append_metric",
    "append_strategy",
    "replay_log",
]
