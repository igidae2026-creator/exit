from __future__ import annotations

from observer.projections import civilization_projection, domain_projection, economy_projection, lineage_projection, replay_projection, runtime_projection, safety_projection, stability_projection, status_projection


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
