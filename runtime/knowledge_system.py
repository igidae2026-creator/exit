from __future__ import annotations

from typing import Any

from genesis.replay import replay_state
from runtime.civilization_state import civilization_state


def accumulated_knowledge() -> dict[str, Any]:
    state = replay_state()
    civilization = civilization_state()
    archive_rows = list((state.get("archive_state", {}) if isinstance(state.get("archive_state"), dict) else {}).items())
    archive_kinds = [str(kind) for kind, _ in archive_rows]
    return {
        "artifact_archives": archive_kinds,
        "lineage_graph": dict((state.get("lineage_state", {}) if isinstance(state.get("lineage_state"), dict) else {}).get("graph", {})),
        "civilization_memory": civilization,
        "references": {
            "artifacts": int(state.get("artifacts", 0)),
            "metrics": int(state.get("metrics", 0)),
            "events": int(state.get("events", 0)),
        },
    }


__all__ = ["accumulated_knowledge"]
