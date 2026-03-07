from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final


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
    target_ticks: int | None
    worker_min: int
    worker_max: int
    target_surviving_lineages: int
    target_active_domains: int
    target_policy_generations: int
    target_evaluation_generations: int
    replay_event_floor: int
    storage_budget_bytes: int
    runtime_budget_bytes: int
    archive_budget_bytes: int


def _profile(
    *,
    name: str,
    default_ticks: int | None,
    tick_seconds: float,
    worker_soft_ceiling: int,
    worker_hard_ceiling: int,
    signal_window: int,
    pressure_window: int,
    metrics_tail: int,
    archive_threshold: int,
    long_run_ticks: int,
    target_ticks: int | None,
    worker_min: int,
    worker_max: int,
    target_surviving_lineages: int,
    target_active_domains: int,
    target_policy_generations: int,
    target_evaluation_generations: int,
    replay_event_floor: int,
    storage_budget_bytes: int,
    runtime_budget_bytes: int,
    archive_budget_bytes: int,
) -> RuntimeProfile:
    return RuntimeProfile(
        name=name,
        default_ticks=default_ticks,
        tick_seconds=tick_seconds,
        worker_soft_ceiling=worker_soft_ceiling,
        worker_hard_ceiling=worker_hard_ceiling,
        signal_window=signal_window,
        pressure_window=pressure_window,
        metrics_tail=metrics_tail,
        archive_threshold=archive_threshold,
        long_run_ticks=long_run_ticks,
        target_ticks=target_ticks,
        worker_min=worker_min,
        worker_max=worker_max,
        target_surviving_lineages=target_surviving_lineages,
        target_active_domains=target_active_domains,
        target_policy_generations=target_policy_generations,
        target_evaluation_generations=target_evaluation_generations,
        replay_event_floor=replay_event_floor,
        storage_budget_bytes=storage_budget_bytes,
        runtime_budget_bytes=runtime_budget_bytes,
        archive_budget_bytes=archive_budget_bytes,
    )


RUNTIME_PROFILES: Final[dict[str, RuntimeProfile]] = {
    "smoke": _profile(
        name="smoke",
        default_ticks=256,
        tick_seconds=0.0,
        worker_soft_ceiling=16,
        worker_hard_ceiling=32,
        signal_window=128,
        pressure_window=128,
        metrics_tail=128,
        archive_threshold=2_048,
        long_run_ticks=256,
        target_ticks=1_000,
        worker_min=8,
        worker_max=32,
        target_surviving_lineages=4,
        target_active_domains=3,
        target_policy_generations=8,
        target_evaluation_generations=8,
        replay_event_floor=10_000,
        storage_budget_bytes=128 * 1024 * 1024,
        runtime_budget_bytes=64 * 1024 * 1024,
        archive_budget_bytes=64 * 1024 * 1024,
    ),
    "bootstrap": _profile(
        name="bootstrap",
        default_ticks=1_000,
        tick_seconds=0.0,
        worker_soft_ceiling=24,
        worker_hard_ceiling=48,
        signal_window=256,
        pressure_window=256,
        metrics_tail=256,
        archive_threshold=4_096,
        long_run_ticks=1_000,
        target_ticks=1_000,
        worker_min=12,
        worker_max=48,
        target_surviving_lineages=4,
        target_active_domains=3,
        target_policy_generations=12,
        target_evaluation_generations=12,
        replay_event_floor=20_000,
        storage_budget_bytes=192 * 1024 * 1024,
        runtime_budget_bytes=96 * 1024 * 1024,
        archive_budget_bytes=96 * 1024 * 1024,
    ),
    "aggressive": _profile(
        name="aggressive",
        default_ticks=5_000,
        tick_seconds=0.0,
        worker_soft_ceiling=48,
        worker_hard_ceiling=96,
        signal_window=512,
        pressure_window=512,
        metrics_tail=512,
        archive_threshold=8_192,
        long_run_ticks=5_000,
        target_ticks=5_000,
        worker_min=24,
        worker_max=96,
        target_surviving_lineages=6,
        target_active_domains=4,
        target_policy_generations=24,
        target_evaluation_generations=24,
        replay_event_floor=50_000,
        storage_budget_bytes=384 * 1024 * 1024,
        runtime_budget_bytes=192 * 1024 * 1024,
        archive_budget_bytes=192 * 1024 * 1024,
    ),
    "soak": _profile(
        name="soak",
        default_ticks=50_000,
        tick_seconds=0.0,
        worker_soft_ceiling=96,
        worker_hard_ceiling=256,
        signal_window=1_024,
        pressure_window=1_024,
        metrics_tail=1_024,
        archive_threshold=16_384,
        long_run_ticks=50_000,
        target_ticks=50_000,
        worker_min=64,
        worker_max=256,
        target_surviving_lineages=8,
        target_active_domains=4,
        target_policy_generations=32,
        target_evaluation_generations=64,
        replay_event_floor=100_000,
        storage_budget_bytes=1_024 * 1024 * 1024,
        runtime_budget_bytes=512 * 1024 * 1024,
        archive_budget_bytes=512 * 1024 * 1024,
    ),
    "production": _profile(
        name="production",
        default_ticks=None,
        tick_seconds=0.05,
        worker_soft_ceiling=256,
        worker_hard_ceiling=1_024,
        signal_window=2_048,
        pressure_window=2_048,
        metrics_tail=2_048,
        archive_threshold=65_536,
        long_run_ticks=100_000,
        target_ticks=None,
        worker_min=256,
        worker_max=1_024,
        target_surviving_lineages=16,
        target_active_domains=8,
        target_policy_generations=128,
        target_evaluation_generations=256,
        replay_event_floor=1_000_000,
        storage_budget_bytes=8 * 1024 * 1024 * 1024,
        runtime_budget_bytes=4 * 1024 * 1024 * 1024,
        archive_budget_bytes=4 * 1024 * 1024 * 1024,
    ),
    "endurance": _profile(
        name="endurance",
        default_ticks=500_000,
        tick_seconds=0.0,
        worker_soft_ceiling=256,
        worker_hard_ceiling=1_024,
        signal_window=4_096,
        pressure_window=4_096,
        metrics_tail=4_096,
        archive_threshold=131_072,
        long_run_ticks=500_000,
        target_ticks=500_000,
        worker_min=256,
        worker_max=1_024,
        target_surviving_lineages=16,
        target_active_domains=8,
        target_policy_generations=128,
        target_evaluation_generations=256,
        replay_event_floor=1_000_000,
        storage_budget_bytes=8 * 1024 * 1024 * 1024,
        runtime_budget_bytes=4 * 1024 * 1024 * 1024,
        archive_budget_bytes=4 * 1024 * 1024 * 1024,
    ),
    "civilization": _profile(
        name="civilization",
        default_ticks=None,
        tick_seconds=0.05,
        worker_soft_ceiling=256,
        worker_hard_ceiling=1_024,
        signal_window=2_048,
        pressure_window=2_048,
        metrics_tail=2_048,
        archive_threshold=65_536,
        long_run_ticks=100_000,
        target_ticks=None,
        worker_min=256,
        worker_max=1_024,
        target_surviving_lineages=16,
        target_active_domains=8,
        target_policy_generations=128,
        target_evaluation_generations=256,
        replay_event_floor=1_000_000,
        storage_budget_bytes=8 * 1024 * 1024 * 1024,
        runtime_budget_bytes=4 * 1024 * 1024 * 1024,
        archive_budget_bytes=4 * 1024 * 1024 * 1024,
    ),
    "run": _profile(
        name="run",
        default_ticks=None,
        tick_seconds=0.05,
        worker_soft_ceiling=256,
        worker_hard_ceiling=1_024,
        signal_window=2_048,
        pressure_window=2_048,
        metrics_tail=2_048,
        archive_threshold=65_536,
        long_run_ticks=100_000,
        target_ticks=None,
        worker_min=256,
        worker_max=1_024,
        target_surviving_lineages=16,
        target_active_domains=8,
        target_policy_generations=128,
        target_evaluation_generations=256,
        replay_event_floor=1_000_000,
        storage_budget_bytes=8 * 1024 * 1024 * 1024,
        runtime_budget_bytes=4 * 1024 * 1024 * 1024,
        archive_budget_bytes=4 * 1024 * 1024 * 1024,
    ),
}


ACTIVE_PROFILE_ALIASES: Final[dict[str, str]] = {
    "run": "production",
    "civilization": "production",
}


def _selected_name(name: str | None, env_name: str, default: str) -> str:
    selected = (name or os.environ.get(env_name) or default).strip().lower()
    return ACTIVE_PROFILE_ALIASES.get(selected, selected)


def active_profile(name: str | None = None) -> RuntimeProfile:
    selected = _selected_name(name, "METAOS_PROFILE", "production")
    return RUNTIME_PROFILES.get(selected, RUNTIME_PROFILES["production"])


def runtime_profile(name: str | None = None) -> RuntimeProfile:
    selected = _selected_name(name, "METAOS_RUNTIME_PROFILE", "smoke")
    return RUNTIME_PROFILES.get(selected, RUNTIME_PROFILES["smoke"])


__all__ = ["RuntimeProfile", "RUNTIME_PROFILES", "active_profile", "runtime_profile"]
