from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class RuntimeProfile:
    name: str
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


RUNTIME_PROFILES: Final[dict[str, RuntimeProfile]] = {
    "smoke": RuntimeProfile(
        name="smoke",
        target_ticks=1_000,
        worker_min=8,
        worker_max=32,
        target_surviving_lineages=2,
        target_active_domains=2,
        target_policy_generations=2,
        target_evaluation_generations=2,
        replay_event_floor=10_000,
        storage_budget_bytes=128 * 1024 * 1024,
        runtime_budget_bytes=64 * 1024 * 1024,
        archive_budget_bytes=64 * 1024 * 1024,
    ),
    "soak": RuntimeProfile(
        name="soak",
        target_ticks=50_000,
        worker_min=64,
        worker_max=256,
        target_surviving_lineages=8,
        target_active_domains=4,
        target_policy_generations=32,
        target_evaluation_generations=64,
        replay_event_floor=100_000,
        storage_budget_bytes=1024 * 1024 * 1024,
        runtime_budget_bytes=512 * 1024 * 1024,
        archive_budget_bytes=512 * 1024 * 1024,
    ),
    "endurance": RuntimeProfile(
        name="endurance",
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
    "civilization": RuntimeProfile(
        name="civilization",
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


def runtime_profile(name: str | None = None) -> RuntimeProfile:
    selected = (name or os.environ.get("METAOS_RUNTIME_PROFILE") or "smoke").strip().lower()
    return RUNTIME_PROFILES.get(selected, RUNTIME_PROFILES["smoke"])


__all__ = ["RuntimeProfile", "RUNTIME_PROFILES", "runtime_profile"]
