from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
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


def _root() -> Path:
    root = os.environ.get("METAOS_ROOT")
    return Path(root) if root else Path(".metaos_runtime")


def _summary_path() -> Path:
    path = _root() / "state" / "civilization_registry_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _registry_path() -> Path:
    if os.environ.get("METAOS_REGISTRY"):
        return Path(os.environ["METAOS_REGISTRY"])
    root = os.environ.get("METAOS_ROOT")
    return Path(root) / "artifact_registry.jsonl" if root else Path(".metaos_runtime/data/artifact_registry.jsonl")


def _archive_path() -> Path:
    if os.environ.get("METAOS_ARCHIVE"):
        return Path(os.environ["METAOS_ARCHIVE"])
    root = os.environ.get("METAOS_ROOT")
    return Path(root) / "archive" / "archive.jsonl" if root else Path(".metaos_runtime/archive/archive.jsonl")


def _stat_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "size": 0, "mtime_ns": 0}
    stat = path.stat()
    return {"exists": True, "size": int(stat.st_size), "mtime_ns": int(stat.st_mtime_ns)}


def _sources_payload() -> dict[str, Any]:
    return {
        "registry": _stat_payload(_registry_path()),
        "archive": _stat_payload(_archive_path()),
    }


def _serialize_state(
    *,
    artifact_counts: Counter[str],
    lineage_counts: Counter[str],
    domain_counts: Counter[str],
    policy_counts: Counter[str],
    evaluation_counts: Counter[str],
    policy_generations: int,
    evaluation_generations: int,
    memory_volume: int,
    shared_artifacts: int,
    external_artifacts: int,
    policy_diffusion_count: int,
    mirrored_external_artifacts: int,
    active_mirrored_artifacts: int,
    hydration_depth_distribution: Counter[int],
    foreign_origin_distribution: Counter[str],
    mirror_lineage_count: int,
    archive_kinds: set[str],
) -> dict[str, Any]:
    total_artifacts = sum(artifact_counts.values()) or 1
    total_domains = sum(domain_counts.values()) or 1
    total_lineages = sum(lineage_counts.values()) or 1
    total_hydration = sum(hydration_depth_distribution.values()) or 1
    knowledge_density = min(1.0, (len(artifact_counts) + len(domain_counts) + len(archive_kinds)) / 24.0)
    memory_growth = min(1.0, memory_volume / 720.0)
    return {
        "artifact_counts": dict(artifact_counts),
        "artifact_distribution": {key: round(value / total_artifacts, 4) for key, value in artifact_counts.items()},
        "lineage_counts": dict(lineage_counts),
        "lineage_distribution": {key: round(value / total_lineages, 4) for key, value in lineage_counts.items()},
        "domain_counts": dict(domain_counts),
        "domain_distribution": {key: round(value / total_domains, 4) for key, value in domain_counts.items()},
        "policy_counts": dict(policy_counts),
        "policy_generations": int(policy_generations),
        "evaluation_counts": dict(evaluation_counts),
        "evaluation_generations": int(evaluation_generations),
        "memory_volume": int(memory_volume),
        "shared_artifacts": int(shared_artifacts),
        "external_artifacts": int(external_artifacts),
        "policy_diffusion_count": int(policy_diffusion_count),
        "mirrored_external_artifacts": int(mirrored_external_artifacts),
        "active_mirrored_artifacts": int(active_mirrored_artifacts),
        "hydration_rate": round(mirrored_external_artifacts / max(1, total_artifacts), 4),
        "hydration_depth_distribution": {str(key): round(value / total_hydration, 4) for key, value in sorted(hydration_depth_distribution.items())},
        "foreign_origin_distribution": dict(foreign_origin_distribution),
        "mirror_lineage_count": int(mirror_lineage_count),
        "memory_growth": round(memory_growth, 4),
        "knowledge_density": round(knowledge_density, 4),
        "_archive_kinds": sorted(kind for kind in archive_kinds if kind),
        "_sources": _sources_payload(),
    }


def _materialize_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_counts": Counter({str(key): int(value) for key, value in dict(summary.get("artifact_counts", {})).items()}),
        "lineage_counts": Counter({str(key): int(value) for key, value in dict(summary.get("lineage_counts", {})).items()}),
        "domain_counts": Counter({str(key): int(value) for key, value in dict(summary.get("domain_counts", {})).items()}),
        "policy_counts": Counter({str(key): int(value) for key, value in dict(summary.get("policy_counts", {})).items()}),
        "evaluation_counts": Counter({str(key): int(value) for key, value in dict(summary.get("evaluation_counts", {})).items()}),
        "policy_generations": int(summary.get("policy_generations", 0)),
        "evaluation_generations": int(summary.get("evaluation_generations", 0)),
        "memory_volume": int(summary.get("memory_volume", 0)),
        "shared_artifacts": int(summary.get("shared_artifacts", 0)),
        "external_artifacts": int(summary.get("external_artifacts", 0)),
        "policy_diffusion_count": int(summary.get("policy_diffusion_count", 0)),
        "mirrored_external_artifacts": int(summary.get("mirrored_external_artifacts", 0)),
        "active_mirrored_artifacts": int(summary.get("active_mirrored_artifacts", 0)),
        "hydration_depth_distribution": Counter({int(key): int(round(float(value) * max(1, int(summary.get("mirrored_external_artifacts", 0) or 1)))) for key, value in dict(summary.get("hydration_depth_distribution", {})).items()}),
        "foreign_origin_distribution": Counter({str(key): int(value) for key, value in dict(summary.get("foreign_origin_distribution", {})).items()}),
        "mirror_lineage_count": int(summary.get("mirror_lineage_count", 0)),
        "archive_kinds": set(str(kind) for kind in summary.get("_archive_kinds", []) if str(kind)),
    }


def _rebuild_summary() -> dict[str, Any]:
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
    archive_kinds: set[str] = set()

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
        kind = str(row.get("kind", ""))
        if kind:
            archive_kinds.add(kind)
        if str(row.get("kind")) in {"memory", "pressure_snapshot", "population_snapshot", "meta_exploration_artifact"}:
            memory_volume += 1
        if str(row.get("visibility", "local")) == "shared":
            shared_artifacts += 1
        if str(row.get("origin_status", "local")) == "external":
            external_artifacts += 1
    artifact_counts["memory"] += memory_volume
    summary = _serialize_state(
        artifact_counts=artifact_counts,
        lineage_counts=lineage_counts,
        domain_counts=domain_counts,
        policy_counts=policy_counts,
        evaluation_counts=evaluation_counts,
        policy_generations=policy_generations,
        evaluation_generations=evaluation_generations,
        memory_volume=memory_volume,
        shared_artifacts=shared_artifacts,
        external_artifacts=external_artifacts,
        policy_diffusion_count=policy_diffusion_count,
        mirrored_external_artifacts=mirrored_external_artifacts,
        active_mirrored_artifacts=active_mirrored_artifacts,
        hydration_depth_distribution=hydration_depth_distribution,
        foreign_origin_distribution=foreign_origin_distribution,
        mirror_lineage_count=mirror_lineage_count,
        archive_kinds=archive_kinds,
    )
    _summary_path().write_text(json.dumps(summary, ensure_ascii=True, sort_keys=True), encoding="utf-8")
    return summary


def _load_summary() -> dict[str, Any] | None:
    path = _summary_path()
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("_sources") != _sources_payload():
        return None
    return payload


def record_registry_row(row: dict[str, Any]) -> None:
    summary = _load_summary()
    state = _materialize_summary(summary) if summary is not None else _materialize_summary(_rebuild_summary())
    artifact_id = str(row.get("artifact_id") or "")
    if not artifact_id:
        return
    artifact_type = str(row.get("artifact_type", row.get("type", "artifact")))
    artifact_class = str(row.get("class", ""))
    if artifact_type == "domain":
        artifact_type = "domain_genome"
    state["artifact_counts"][artifact_type if artifact_type in _CANONICAL_TYPES else "artifact"] += 1
    payload = row.get("payload", {}) if isinstance(row.get("payload"), dict) else {}
    metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata"), dict) else {}
    parent_ids = row.get("parent_ids", ((row.get("refs") or {}).get("parents", []))) if isinstance(row.get("refs"), dict) else row.get("parent_ids", [])
    lineage_id = str(row.get("lineage_id") or metadata.get("lineage_id") or ((parent_ids or [artifact_id])[0]))
    state["lineage_counts"][lineage_id] += 1
    genome = payload.get("genome", {}) if isinstance(payload.get("genome"), dict) else {}
    routing = payload.get("routing", {}) if isinstance(payload.get("routing"), dict) else {}
    domain = str(row.get("domain") or payload.get("domain") or routing.get("selected_domain") or genome.get("name") or "default")
    state["domain_counts"][domain] += 1
    if artifact_class == "policy" or artifact_type == "policy" or artifact_type.endswith("_policy") or artifact_type == "runtime_policy":
        state["policy_generations"] += 1
        state["policy_counts"][artifact_type] += 1
        state["policy_diffusion_count"] += int(bool((((row.get("payload") or {}).get("policy") or {}).get("policy_origin"))))
    if artifact_class == "evaluation" or artifact_type.startswith("evaluation"):
        state["evaluation_generations"] += 1
        state["evaluation_counts"][artifact_type] += 1
    payload_visibility = str((row.get("payload", {}) if isinstance(row.get("payload"), dict) else {}).get("visibility", row.get("visibility", "local")))
    if payload_visibility == "shared":
        state["shared_artifacts"] += 1
    if payload_visibility == "external":
        state["external_artifacts"] += 1
    if str(row.get("artifact_scope", "")) == "mirrored":
        state["mirrored_external_artifacts"] += 1
        state["mirror_lineage_count"] += 1
        state["hydration_depth_distribution"][int(row.get("hydration_depth", 0) or 0)] += 1
        if str(row.get("origin_node", "")):
            state["foreign_origin_distribution"][str(row.get("origin_node", ""))] += 1
        if str(metadata.get("external_status") or payload.get("external_status") or "") == "activated":
            state["active_mirrored_artifacts"] += 1
    _summary_path().write_text(json.dumps(_serialize_state(**state), ensure_ascii=True, sort_keys=True), encoding="utf-8")


def record_archive_row(row: dict[str, Any]) -> None:
    summary = _load_summary()
    state = _materialize_summary(summary) if summary is not None else _materialize_summary(_rebuild_summary())
    kind = str(row.get("kind", ""))
    if kind:
        state["archive_kinds"].add(kind)
    if kind in {"memory", "pressure_snapshot", "population_snapshot", "meta_exploration_artifact"}:
        state["memory_volume"] += 1
        state["artifact_counts"]["memory"] += 1
    if str(row.get("visibility", "local")) == "shared":
        state["shared_artifacts"] += 1
    if str(row.get("origin_status", "local")) == "external":
        state["external_artifacts"] += 1
    _summary_path().write_text(json.dumps(_serialize_state(**state), ensure_ascii=True, sort_keys=True), encoding="utf-8")


def civilization_state() -> dict[str, Any]:
    summary = _load_summary()
    if summary is None:
        summary = _rebuild_summary()
    return {key: value for key, value in summary.items() if not str(key).startswith("_")}


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
