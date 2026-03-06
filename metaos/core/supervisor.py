from __future__ import annotations

from typing import Any, Callable

from kernel.recovery import replay_restore
from kernel.supervisor import guarded_step as _guarded_step


def save_checkpoint(state: Any) -> Any:
    return state


def load_checkpoint(default: Any = None) -> Any:
    return replay_restore(default=default)


def guarded_step(step_fn: Callable[[Any], Any], state: Any, on_fail: Callable[[Any], Any] | None = None) -> Any:
    out = _guarded_step(step_fn, state, on_fail=on_fail)
    if isinstance(out, dict) and out.get("mode") == "safe_mode":
        restored = load_checkpoint(default=state)
        if isinstance(restored, dict):
            merged = dict(restored)
            merged.setdefault("supervisor_mode", "safe_mode")
            return merged
        return restored
    return out
