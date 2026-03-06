from __future__ import annotations

from typing import Any, Mapping, Sequence


def signal_sources(history: Sequence[Mapping[str, Any]] | None = None, metrics: Mapping[str, Any] | None = None) -> dict[str, Any]:
    rows = list(history or [])
    return {
        "history": rows[-64:],
        "metrics": dict(metrics or {}),
    }

