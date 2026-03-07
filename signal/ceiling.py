from __future__ import annotations

from typing import Any, Mapping

from runtime.profiles import active_profile


def worker_ceiling(pressure: Mapping[str, float], guard: Mapping[str, Any] | None = None, *, profile: str | None = None) -> int:
    guard = dict(guard or {})
    profile_cfg = active_profile(profile)
    if guard.get("downshift_workers"):
        return max(8, profile_cfg.worker_soft_ceiling // 2)
    combined = float(pressure.get("novelty_pressure", 0.0)) + float(pressure.get("diversity_pressure", 0.0)) + float(pressure.get("domain_shift_pressure", 0.0))
    return profile_cfg.worker_hard_ceiling if combined >= 2.2 else profile_cfg.worker_soft_ceiling
