from __future__ import annotations

from typing import Any, Mapping

from core.event_log import append_event, append_metric


def log_event(event_type: str, payload: Mapping[str, Any], *, data_dir: str = "data") -> dict[str, Any]:
    return append_event(event_type, payload, data_dir=data_dir)


def log_metrics(payload: Mapping[str, Any], *, data_dir: str = "data") -> dict[str, Any]:
    return append_metric(payload, data_dir=data_dir)
