from __future__ import annotations

from typing import Any

from federation.federation_hydration import replay_hydrated_artifacts


def federation_replay_state() -> dict[str, Any]:
    hydrated = replay_hydrated_artifacts()
    return {
        "hydrated_artifacts": hydrated,
        "mirrored_external_artifacts": len(hydrated),
        "active_mirrored_artifacts": sum(1 for row in hydrated if bool(row.get("active"))),
        "replay_ok": True,
    }


__all__ = ["federation_replay_state"]
