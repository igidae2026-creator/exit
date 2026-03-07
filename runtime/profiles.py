from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeProfile:
    name: str
    default_ticks: int | None
    tick_seconds: float
    worker_soft_ceiling: int
    worker_hard_ceiling: int
    signal_window: int
    pressure_window: int
    metrics_tail: int
    archive_threshold: int
    long_run_ticks: int


PROFILES: dict[str, RuntimeProfile] = {
    "smoke": RuntimeProfile(
        name="smoke",
        default_ticks=32,
        tick_seconds=0.01,
        worker_soft_ceiling=16,
        worker_hard_ceiling=32,
        signal_window=64,
        pressure_window=64,
        metrics_tail=64,
        archive_threshold=1024,
        long_run_ticks=120,
    ),
    "run": RuntimeProfile(
        name="run",
        default_ticks=None,
        tick_seconds=0.05,
        worker_soft_ceiling=64,
        worker_hard_ceiling=128,
        signal_window=256,
        pressure_window=128,
        metrics_tail=128,
        archive_threshold=4096,
        long_run_ticks=2000,
    ),
    "soak": RuntimeProfile(
        name="soak",
        default_ticks=2000,
        tick_seconds=0.0,
        worker_soft_ceiling=96,
        worker_hard_ceiling=192,
        signal_window=512,
        pressure_window=256,
        metrics_tail=256,
        archive_threshold=8192,
        long_run_ticks=10000,
    ),
}


def active_profile(name: str | None = None) -> RuntimeProfile:
    selected = (name or os.getenv("METAOS_PROFILE") or "run").strip().lower()
    return PROFILES.get(selected, PROFILES["run"])
