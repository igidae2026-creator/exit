from __future__ import annotations

from collections import Counter
from typing import Any

from artifact.archive import load_archive
from artifact.registry import rows


_CANONICAL_TYPES = (
    "artifact",
    "output",
    "strategy",
    "policy",
    "quest",
    "evaluation",
    "repair",
    "allocator",
    "domain_genome",
    "memory",
)


def civilization_state() -> dict[str, Any]:
    artifact_counts: Counter[str] = Counter()
    lineage_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    policy_counts: Counter[str] = Counter()
    evaluation_counts: Counter[str] = Counter()
    policy_generations = 0
    evaluation_generations = 0
    memory_volume = 0
    shared_artifacts = 0
    external_artifacts = 0
    policy_diffusion_count = 0
    mirrored_external_artifacts = 0
    active_mirrored_artifacts = 0
    hydration_depth_distribution: Counter[int] = Counter()
    foreign_origin_distribution: Counter[str] = Counter()
    mirror_lineage_count = 0

    for row in rows():
        artifact_id = str(row.get("artifact_id") or "")
        if not artifact_id:
            continue
        artifact_type = str(row.get("artifact_type", row.get("type", "artifact")))
        artifact_class = str(row.get("class", ""))
        if artifact_type == "domain":
            artifact_type = "domain_genome"
        artifact_counts[artifact_type if artifact_type in _CANONICAL_TYPES else "artifact"] += 1
        payload = row.get("payload", {}) if isinstance(row.get("payload"), dict) else {}
        metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata"), dict) else {}
        parent_ids = row.get("parent_ids", ((row.get("refs") or {}).get("parents", []))) if isinstance(row.get("refs"), dict) else row.get("parent_ids", [])
        lineage_id = str(metadata.get("lineage_id") or ((parent_ids or [artifact_id])[0]))
        lineage_counts[lineage_id] += 1
        genome = payload.get("genome", {}) if isinstance(payload.get("genome"), dict) else {}
        routing = payload.get("routing", {}) if isinstance(payload.get("routing"), dict) else {}
        domain = str(payload.get("domain") or routing.get("selected_domain") or genome.get("name") or "default")
        domain_counts[domain] += 1
        if artifact_class == "policy" or artifact_type == "policy" or artifact_type.endswith("_policy") or artifact_type == "runtime_policy":
            policy_generations += 1
            policy_counts[artifact_type] += 1
            policy_diffusion_count += int(bool((((row.get("payload") or {}).get("policy") or {}).get("policy_origin"))))
        if artifact_class == "evaluation" or artifact_type.startswith("evaluation"):
            evaluation_generations += 1
            evaluation_counts[artifact_type] += 1
        payload_visibility = str((row.get("payload", {}) if isinstance(row.get("payload"), dict) else {}).get("visibility", row.get("visibility", "local")))
        if payload_visibility == "shared":
            shared_artifacts += 1
        if payload_visibility == "external":
            external_artifacts += 1
        if str(row.get("artifact_scope", "")) == "mirrored":
            mirrored_external_artifacts += 1
            mirror_lineage_count += 1
            hydration_depth_distribution[int(row.get("hydration_depth", 0) or 0)] += 1
            if str(row.get("origin_node", "")):
                foreign_origin_distribution[str(row.get("origin_node", ""))] += 1
            if str(metadata.get("external_status") or payload.get("external_status") or "") == "activated":
                active_mirrored_artifacts += 1

    for row in load_archive():
        if str(row.get("kind")) in {"memory", "pressure_snapshot", "population_snapshot", "meta_exploration_artifact"}:
            memory_volume += 1
        if str(row.get("visibility", "local")) == "shared":
            shared_artifacts += 1
        if str(row.get("origin_status", "local")) == "external":
            external_artifacts += 1
    artifact_counts["memory"] += memory_volume
    total_artifacts = sum(artifact_counts.values()) or 1
    total_domains = sum(domain_counts.values()) or 1
    total_lineages = sum(lineage_counts.values()) or 1
    archive_kinds = {str(row.get("kind", "")) for row in load_archive() if row.get("kind")}
    knowledge_density = min(1.0, (len(artifact_counts) + len(domain_counts) + len(archive_kinds)) / 24.0)
    memory_growth = min(1.0, memory_volume / 720.0)
    total_hydration = sum(hydration_depth_distribution.values()) or 1
    return {
        "artifact_counts": dict(artifact_counts),
        "artifact_distribution": {key: round(value / total_artifacts, 4) for key, value in artifact_counts.items()},
        "lineage_counts": dict(lineage_counts),
        "lineage_distribution": {key: round(value / total_lineages, 4) for key, value in lineage_counts.items()},
        "domain_counts": dict(domain_counts),
        "domain_distribution": {key: round(value / total_domains, 4) for key, value in domain_counts.items()},
        "policy_counts": dict(policy_counts),
        "policy_generations": policy_generations,
        "evaluation_counts": dict(evaluation_counts),
        "evaluation_generations": evaluation_generations,
        "memory_volume": memory_volume,
        "shared_artifacts": shared_artifacts,
        "external_artifacts": external_artifacts,
        "policy_diffusion_count": policy_diffusion_count,
        "mirrored_external_artifacts": mirrored_external_artifacts,
        "active_mirrored_artifacts": active_mirrored_artifacts,
        "hydration_rate": round(mirrored_external_artifacts / max(1, total_artifacts), 4),
        "hydration_depth_distribution": {str(key): round(value / total_hydration, 4) for key, value in sorted(hydration_depth_distribution.items())},
        "foreign_origin_distribution": dict(foreign_origin_distribution),
        "mirror_lineage_count": mirror_lineage_count,
        "memory_growth": round(memory_growth, 4),
        "knowledge_density": round(knowledge_density, 4),
    }


def civilization_memory_snapshot() -> dict[str, Any]:
    state = civilization_state()
    return {
        "artifact_distribution": dict(state.get("artifact_distribution", {})),
        "domain_distribution": dict(state.get("domain_distribution", {})),
        "policy_generations": int(state.get("policy_generations", 0)),
        "evaluation_generations": int(state.get("evaluation_generations", 0)),
        "lineage_counts": dict(state.get("lineage_counts", {})),
        "memory_volume": int(state.get("memory_volume", 0)),
        "shared_artifacts": int(state.get("shared_artifacts", 0)),
        "external_artifacts": int(state.get("external_artifacts", 0)),
        "policy_diffusion_count": int(state.get("policy_diffusion_count", 0)),
        "mirrored_external_artifacts": int(state.get("mirrored_external_artifacts", 0)),
        "active_mirrored_artifacts": int(state.get("active_mirrored_artifacts", 0)),
        "hydration_rate": float(state.get("hydration_rate", 0.0)),
        "hydration_depth_distribution": dict(state.get("hydration_depth_distribution", {})),
        "foreign_origin_distribution": dict(state.get("foreign_origin_distribution", {})),
        "mirror_lineage_count": int(state.get("mirror_lineage_count", 0)),
        "memory_growth": float(state.get("memory_growth", 0.0)),
        "knowledge_density": float(state.get("knowledge_density", 0.0)),
    }


__all__ = ["civilization_memory_snapshot", "civilization_state"]
