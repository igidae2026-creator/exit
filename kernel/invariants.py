from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from kernel.replay import replay_state
from kernel.spine import iter_truth_paths, read_artifact_log


def immutable_artifacts() -> dict[str, Any]:
    rows = read_artifact_log()
    duplicates: dict[str, int] = {}
    seen: set[str] = set()
    for row in rows:
        artifact_id = str(row.get("artifact_id") or "")
        if not artifact_id:
            continue
        if artifact_id in seen:
            duplicates[artifact_id] = duplicates.get(artifact_id, 1) + 1
        seen.add(artifact_id)
    return {"ok": not duplicates, "duplicates": duplicates}


def append_only_logs() -> dict[str, Any]:
    paths = list(iter_truth_paths())
    stats = {str(path): {"exists": path.exists(), "size": path.stat().st_size if path.exists() else 0} for path in paths}
    return {"ok": all(item["exists"] for item in stats.values()), "paths": stats}


def replay_determinism() -> dict[str, Any]:
    state_a = replay_state()
    state_b = replay_state()
    digest_a = hashlib.sha256(json.dumps(state_a, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()
    digest_b = hashlib.sha256(json.dumps(state_b, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()
    return {"ok": digest_a == digest_b, "digest": digest_a}


def lineage_survival_floor(minimum: int = 2) -> dict[str, Any]:
    state = replay_state()
    surviving = int((state.get("lineage_state", {}) if isinstance(state.get("lineage_state"), Mapping) else {}).get("surviving_lineages", 0))
    return {"ok": surviving >= int(minimum), "surviving_lineages": surviving, "minimum": int(minimum)}


def enforce(minimum_lineages: int = 2) -> dict[str, Any]:
    artifact_check = immutable_artifacts()
    append_check = append_only_logs()
    replay_check = replay_determinism()
    lineage_check = lineage_survival_floor(minimum_lineages)
    ok = all(check["ok"] for check in (artifact_check, append_check, replay_check, lineage_check))
    return {
        "ok": ok,
        "immutable_artifacts": artifact_check,
        "append_only_logs": append_check,
        "replay_determinism": replay_check,
        "lineage_survival_floor": lineage_check,
    }
