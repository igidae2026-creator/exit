from __future__ import annotations

from typing import Any

from runtime.observability import (
    civilization_summary,
    domain_summary,
    economy_summary,
    lineage_summary,
    pressure_summary,
    replay_summary,
    safety_status,
    stability_status,
    runtime_summary,
)


def status_projection() -> dict[str, Any]:
    return runtime_summary()


def runtime_projection() -> dict[str, Any]:
    return runtime_summary()


def civilization_projection() -> dict[str, Any]:
    return civilization_summary()


def lineage_projection() -> dict[str, Any]:
    return lineage_summary()


def domain_projection() -> dict[str, Any]:
    return domain_summary()


def pressure_projection() -> dict[str, Any]:
    return pressure_summary()


def economy_projection() -> dict[str, Any]:
    return economy_summary()


def replay_projection() -> dict[str, Any]:
    return replay_summary()


def stability_projection() -> dict[str, Any]:
    return stability_status()


def safety_projection() -> dict[str, Any]:
    return safety_status()
