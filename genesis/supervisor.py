from __future__ import annotations

import os
import traceback
from typing import Any, Callable

from genesis.replay import replay_state


def _invalid_state(state: Any) -> bool:
    if not isinstance(state, dict):
        return False
    workers = int(state.get("workers", 1))
    return workers <= 0 or ("pressure" in state and not isinstance(state.get("pressure"), dict))


def _escalate(state: Any) -> Any:
    if not isinstance(state, dict):
        return state
    out = dict(state)
    pressure = dict(out.get("pressure", {})) if isinstance(out.get("pressure"), dict) else {}
    lineage = int((out.get("lineage_state", {}) if isinstance(out.get("lineage_state"), dict) else {}).get("surviving_lineages", 2))
    if lineage <= 1:
        pressure["diversity_pressure"] = max(0.85, float(pressure.get("diversity_pressure", 0.0)))
    if bool(out.get("plateau")):
        out["quest"] = {"type": "reframing", "reason": "plateau"}
    repair = out.get("repair")
    if isinstance(repair, dict) and repair.get("failed"):
        out["quest"] = {"type": "repair", "escalation": "repair_failure"}
    out["pressure"] = pressure
    return out


def replay_restore(default: Any = None) -> Any:
    if not any(os.environ.get(name) for name in ("METAOS_EVENT_LOG", "METAOS_METRICS", "METAOS_REGISTRY", "METAOS_ARCHIVE", "METAOS_ROOT")):
        return default
    restored = replay_state()
    if not restored or (restored.get("events", 0) == 0 and restored.get("metrics", 0) == 0 and restored.get("artifacts", 0) == 0):
        return default
    return restored


def rollback(state: Any, fallback: Any) -> Any:
    return fallback if fallback is not None else state


def safe_mode(state: Any) -> dict[str, Any]:
    return {"mode": "safe_mode", "state": state}


def guarded_step(step_fn: Callable[[Any], Any], state: Any, on_fail: Callable[[Any], Any] | None = None) -> Any:
    if _invalid_state(state):
        restored = replay_restore(default=state)
        return safe_mode(restored)
    try:
        return step_fn(state)
    except Exception:
        traceback.print_exc()
        repaired = _escalate(state)
        if on_fail is not None:
            try:
                repaired = on_fail(repaired)
            except Exception:
                traceback.print_exc()
        try:
            return step_fn(repaired)
        except Exception:
            traceback.print_exc()
            restored = rollback(state, replay_restore(default=repaired))
            if on_fail is not None and restored is not None:
                return restored
            return safe_mode(restored)


__all__ = ["guarded_step", "replay_restore", "rollback", "safe_mode"]
