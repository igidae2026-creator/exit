from __future__ import annotations

from typing import Any, Mapping


def validate_runtime_gates(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {"name": "gates", "ok": bool(payload.get("tick_boundary_only", True))}
