from __future__ import annotations

from observer.projections import civilization_projection, domain_projection, economy_projection, ecosystem_projection, external_artifact_projection, external_domain_projection, external_policy_projection, federation_adoption_projection, federation_projection, foreign_origin_projection, hydration_guardrail_projection, hydration_projection, lineage_projection, mirrored_artifact_projection, node_projection, replay_projection, runtime_projection, safety_projection, stability_projection, status_projection, transport_projection


def read_status() -> dict[str, object]:
    return status_projection()


def read_civilization_status() -> dict[str, object]:
    return civilization_projection()


def read_lineage_status() -> dict[str, object]:
    return lineage_projection()


def read_domain_status() -> dict[str, object]:
    return domain_projection()


def read_economy_status() -> dict[str, object]:
    return economy_projection()


def read_runtime_status() -> dict[str, object]:
    return runtime_projection()


def read_replay_status() -> dict[str, object]:
    return replay_projection()


def read_stability_status() -> dict[str, object]:
    return stability_projection()


def read_safety_status() -> dict[str, object]:
    return safety_projection()


def read_federation_status() -> dict[str, object]:
    return federation_projection()


def read_node_status() -> dict[str, object]:
    return node_projection()


def read_topology_status() -> dict[str, object]:
    federation = federation_projection()
    return dict(federation.get("federation_topology", federation.get("node_topology", {})))


def read_federation_adoption_status() -> dict[str, object]:
    return federation_adoption_projection()


def read_external_artifact_status() -> dict[str, object]:
    return external_artifact_projection()


def read_external_policy_status() -> dict[str, object]:
    return external_policy_projection()


def read_external_domain_status() -> dict[str, object]:
    return external_domain_projection()


def read_transport_status() -> dict[str, object]:
    return transport_projection()


def read_hydration_status() -> dict[str, object]:
    return hydration_projection()


def read_mirrored_artifact_status() -> dict[str, object]:
    return mirrored_artifact_projection()


def read_foreign_origin_status() -> dict[str, object]:
    return foreign_origin_projection()


def read_hydration_guardrail_status() -> dict[str, object]:
    return hydration_guardrail_projection()


def read_ecosystem_status() -> dict[str, object]:
    return ecosystem_projection()
