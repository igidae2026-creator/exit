from __future__ import annotations

from typing import Any

from artifact.lineage import build_lineage_view
from kernel.spine import read_artifact_log, read_events, read_metrics


def replay_state() -> dict[str, Any]:
    events = read_events()
    metrics = read_metrics()
    artifacts = read_artifact_log()
    last_event = events[-1] if events else {}
    last_metrics = metrics[-1] if metrics else {}
    lineage = build_lineage_view(artifacts)
    return {
        "tick": int((last_metrics or {}).get("tick") or (last_event.get("payload", {}) if isinstance(last_event.get("payload"), dict) else {}).get("tick", 0) or 0),
        "events": len(events),
        "metrics": len(metrics),
        "artifacts": len(artifacts),
        "artifact_classes": {str(row.get("class", "")): 0 for row in artifacts},
        "lineage": lineage,
        "last_event": last_event,
        "last_metrics": last_metrics,
    }

