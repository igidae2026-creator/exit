from __future__ import annotations

from typing import Any

from ecosystem.ecosystem_state import ecosystem_state
from federation.federation_state import federation_state
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


def federation_projection() -> dict[str, Any]:
    return federation_state()


def node_projection() -> dict[str, Any]:
    state = federation_state()
    return {
        "node_count": len(list(state.get("federation_nodes", []))),
        "artifact_exchange_rate": float(state.get("artifact_exchange_rate", 0.0)),
        "domain_propagation_rate": float(state.get("domain_propagation_rate", 0.0)),
    }


def ecosystem_projection() -> dict[str, Any]:
    return ecosystem_state()
