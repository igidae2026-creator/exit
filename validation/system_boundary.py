from __future__ import annotations

from typing import Any, Mapping

from validation.boundary import validate_boundary


def validate_system_boundary(payload: Mapping[str, Any]) -> dict[str, Any]:
    return validate_boundary(payload)
