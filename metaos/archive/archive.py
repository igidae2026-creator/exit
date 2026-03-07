from __future__ import annotations

from typing import Any

from artifact.archive import save as _save


def save(kind: str, payload: Any, *, visibility: str = "local", origin_status: str = "local") -> None:
    _save(kind, payload, visibility=visibility, origin_status=origin_status)


__all__ = ["save"]
