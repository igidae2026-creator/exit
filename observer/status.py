from __future__ import annotations

from observer.projections import civilization_projection, domain_projection, lineage_projection, replay_projection, status_projection


def read_status() -> dict[str, object]:
    return status_projection()


def read_civilization_status() -> dict[str, object]:
    return civilization_projection()


def read_lineage_status() -> dict[str, object]:
    return lineage_projection()


def read_domain_status() -> dict[str, object]:
    return domain_projection()


def read_replay_status() -> dict[str, object]:
    return replay_projection()
