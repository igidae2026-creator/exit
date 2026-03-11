from __future__ import annotations

from typing import Any

from ecosystem.ecosystem_state import ecosystem_state
from federation.federation_state import federation_state
from runtime.observability import (
    civilization_summary,
    consumer_intervention_apply_status,
    consumer_status,
    consumer_intervention_status,
    domain_summary,
    economy_summary,
    external_artifact_status,
    external_domain_status,
    external_policy_status,
    foreign_origin_status,
    federation_adoption_status,
    federation_summary,
    hydration_guardrail_status,
    hydration_status,
    lineage_summary,
    mirrored_artifact_status,
    node_summary,
    pressure_summary,
    replay_summary,
    safety_status,
    stability_status,
    transport_status,
    runtime_summary,
)


def status_projection() -> dict[str, Any]:
    return runtime_summary()


def runtime_projection() -> dict[str, Any]:
    return runtime_summary()


def consumer_projection() -> dict[str, Any]:
    return consumer_status()


def consumer_intervention_projection() -> dict[str, Any]:
    return consumer_intervention_status()


def consumer_intervention_apply_projection() -> dict[str, Any]:
    return consumer_intervention_apply_status()


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
    return federation_summary()


def node_projection() -> dict[str, Any]:
    return node_summary()


def ecosystem_projection() -> dict[str, Any]:
    return ecosystem_state()


def federation_adoption_projection() -> dict[str, Any]:
    return federation_adoption_status()


def external_artifact_projection() -> dict[str, Any]:
    return external_artifact_status()


def external_policy_projection() -> dict[str, Any]:
    return external_policy_status()


def external_domain_projection() -> dict[str, Any]:
    return external_domain_status()


def transport_projection() -> dict[str, Any]:
    return transport_status()


def hydration_projection() -> dict[str, Any]:
    return hydration_status()


def mirrored_artifact_projection() -> dict[str, Any]:
    return mirrored_artifact_status()


def foreign_origin_projection() -> dict[str, Any]:
    return foreign_origin_status()


def hydration_guardrail_projection() -> dict[str, Any]:
    return hydration_guardrail_status()
