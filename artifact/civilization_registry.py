from __future__ import annotations

from collections import Counter
from typing import Any

from artifact.archive import load_archive
from artifact.registry import load_envelope, rows


_CANONICAL_TYPES = (
    "artifact",
    "strategy",
    "policy",
    "quest",
    "evaluation",
    "allocator",
    "domain_genome",
    "memory",
)


def civilization_state() -> dict[str, Any]:
    artifact_counts: Counter[str] = Counter()
    lineage_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    policy_generations = 0
    memory_volume = 0

    for row in rows():
        artifact_id = str(row.get("artifact_id") or "")
        if not artifact_id:
            continue
        envelope = load_envelope(artifact_id)
        if not envelope:
            continue
        artifact_type = str(envelope.get("artifact_type", envelope.get("type", "artifact")))
        if artifact_type == "domain":
            artifact_type = "domain_genome"
        artifact_counts[artifact_type if artifact_type in _CANONICAL_TYPES else "artifact"] += 1
        payload = envelope.get("payload", {}) if isinstance(envelope.get("payload"), dict) else {}
        metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata"), dict) else {}
        lineage_id = str(metadata.get("lineage_id") or (envelope.get("parent_ids") or [artifact_id])[0])
        lineage_counts[lineage_id] += 1
        domain = str(payload.get("domain") or (payload.get("routing", {}) if isinstance(payload.get("routing"), dict) else {}).get("selected_domain") or "default")
        domain_counts[domain] += 1
        if artifact_type == "policy":
            policy_generations += 1

    for row in load_archive():
        if str(row.get("kind")) in {"memory", "pressure_snapshot", "population_snapshot", "meta_exploration_artifact"}:
            memory_volume += 1
    artifact_counts["memory"] += memory_volume
    return {
        "artifact_counts": dict(artifact_counts),
        "lineage_counts": dict(lineage_counts),
        "domain_counts": dict(domain_counts),
        "policy_generations": policy_generations,
        "memory_volume": memory_volume,
    }
