from __future__ import annotations

from typing import Any, Mapping


def worker_ceiling(pressure: Mapping[str, float], guard: Mapping[str, Any] | None = None) -> int:
    guard = dict(guard or {})
    if guard.get("downshift_workers"):
        return 12
    combined = float(pressure.get("novelty_pressure", 0.0)) + float(pressure.get("diversity_pressure", 0.0)) + float(pressure.get("domain_shift_pressure", 0.0))
    return 32 if combined >= 2.2 else 28

