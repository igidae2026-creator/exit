from __future__ import annotations

import collections
import json
import os
from pathlib import Path
from typing import Any


def _metrics_path() -> Path:
    return Path(os.environ.get("METAOS_METRICS", ".metaos_runtime/data/metrics.jsonl"))


def tail(n: int = 200) -> list[dict[str, Any]]:
    buf: collections.deque[dict[str, Any]] = collections.deque(maxlen=n)
    path = _metrics_path()
    if not path.exists():
        return list(buf)
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                buf.append(json.loads(line))
            except Exception:
                pass
    return list(buf)


def _metric_values(window: int, key: str) -> list[float]:
    values: list[float] = []
    for row in tail(window)[-window:]:
        if isinstance(row, dict) and key in row:
            values.append(float(row.get(key, 0.0)))
        else:
            payload = row.get("payload", {}) if isinstance(row, dict) and isinstance(row.get("payload"), dict) else {}
            values.append(float(payload.get(key, 0.0)))
    return values


def plateau(window: int = 50, eps: float = 0.02) -> bool:
    vals = _metric_values(window, "score")
    if len(vals) < max(10, window // 2):
        return False
    return (max(vals) - min(vals)) <= eps


def novelty_drop(window: int = 50, threshold: float = 0.35) -> bool:
    vals = _metric_values(window, "novelty")
    if not vals:
        return False
    return (sum(vals) / len(vals)) < threshold


def failure_spike(window: int = 50, threshold: float = 0.2) -> bool:
    vals = _metric_values(window, "fail_rate")
    if not vals:
        return False
    return (sum(vals) / len(vals)) > threshold
