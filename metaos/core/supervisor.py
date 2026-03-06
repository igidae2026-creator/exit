from __future__ import annotations

import json
import os
import traceback
from pathlib import Path
from typing import Any, Callable


def _checkpoint_path() -> Path:
    path = Path(os.environ.get("METAOS_CHECKPOINT", ".metaos_runtime/state/checkpoint.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_checkpoint(state: Any) -> None:
    with _checkpoint_path().open("w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=True)


def load_checkpoint(default: Any = None) -> Any:
    path = _checkpoint_path()
    if not path.exists():
        return {} if default is None else default
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {} if default is None else default


def guarded_step(step_fn: Callable[[Any], Any], state: Any, on_fail: Callable[[Any], Any] | None = None) -> Any:
    try:
        out = step_fn(state)
        save_checkpoint(out or state)
        return out
    except Exception:
        traceback.print_exc()
        restored = load_checkpoint(default=state)
        if on_fail:
            try:
                return on_fail(restored)
            except Exception:
                traceback.print_exc()
        return restored
