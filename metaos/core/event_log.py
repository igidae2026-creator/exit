from __future__ import annotations

from typing import Any, Mapping

from kernel.spine import append_event


def emit(event_type: str, payload: Mapping[str, Any]) -> None:
    append_event(event_type, payload)
