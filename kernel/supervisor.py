from __future__ import annotations

import traceback
from typing import Any, Callable

from kernel.recovery import rollback, safe_mode


def guarded_step(step_fn: Callable[[Any], Any], state: Any, on_fail: Callable[[Any], Any] | None = None) -> Any:
    try:
        return step_fn(state)
    except Exception:
        traceback.print_exc()
        restored = rollback(state, state)
        if on_fail is not None:
            try:
                return on_fail(restored)
            except Exception:
                traceback.print_exc()
        return safe_mode(restored)
