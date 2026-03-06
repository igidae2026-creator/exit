from __future__ import annotations

from observer.projections import status_projection


def read_status() -> dict[str, object]:
    return status_projection()

