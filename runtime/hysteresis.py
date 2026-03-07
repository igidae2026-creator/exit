from __future__ import annotations


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def smooth(value: float, prev: float | None = None, alpha: float = 0.2) -> float:
    if prev is None:
        return float(value)
    alpha = clamp01(alpha)
    return float(prev) + (alpha * (float(value) - float(prev)))


def bounded_step(
    current: float,
    target: float,
    max_delta: float = 0.08,
    lo: float = 0.0,
    hi: float = 1.0,
) -> float:
    current = float(current)
    target = float(target)
    step = max(-abs(max_delta), min(abs(max_delta), target - current))
    return max(lo, min(hi, current + step))


def cooldown(active_ticks: int, cooldown_ticks: int) -> bool:
    return int(active_ticks) >= max(1, int(cooldown_ticks))
