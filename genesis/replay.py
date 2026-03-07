from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


CANONICAL_PRESSURE_KEYS = (
    "novelty_pressure",
    "diversity_pressure",
    "efficiency_pressure",
    "repair_pressure",
    "domain_shift_pressure",
    "reframing_pressure",
)

_REPLAY_CACHE_KEY: tuple[tuple[str, bool, int, int], ...] | None = None
_REPLAY_CACHE_VALUE: dict[str, Any] | None = None


def _active_root() -> Path | None:
    root = os.environ.get("METAOS_ROOT")
    if not root:
        return None
    return Path(root).expanduser().resolve()


def _canonical_path(env_name: str, root_filename: str, default_path: str) -> Path:
    explicit = os.environ.get(env_name)
    if explicit:
        return Path(explicit).expanduser().resolve()
    root = _active_root()
    if root is not None:
        return root / root_filename
    return Path(default_path)


def _canonical_paths() -> dict[str, Path]:
    return {
        "event_log": _canonical_path("METAOS_EVENT_LOG", "events.jsonl", ".metaos_runtime/data/events.jsonl"),
        "metrics": _canonical_path("METAOS_METRICS", "metrics.jsonl", ".metaos_runtime/data/metrics.jsonl"),
        "registry": _canonical_path("METAOS_REGISTRY", "artifact_registry.jsonl", ".metaos_runtime/data/artifact_registry.jsonl"),
        "archive": _canonical_path("METAOS_ARCHIVE", "archive.jsonl", ".metaos_runtime/archive/archive.jsonl"),
        "signals": _canonical_path("METAOS_SIGNALS", "signals.jsonl", ".metaos_runtime/data/signals.jsonl"),
    }


def _path_signature(path: Path) -> tuple[str, bool, int, int]:
    if not path.exists():
        return (str(path), False, 0, 0)
    stat = path.stat()
    return (str(path), True, int(stat.st_size), int(stat.st_mtime_ns))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _artifact_envelopes(registry_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in registry_rows:
        artifact_id = str(row.get("artifact_id") or "")
        if not artifact_id:
            continue
        out.append(
            {
                **dict(row),
                "artifact_id": artifact_id,
                "artifact_type": row.get("artifact_type", row.get("type")),
                "parent_ids": list(row.get("parent_ids", ((row.get("refs") or {}).get("parents", [])))),
                "payload": dict(row.get("payload", {})) if isinstance(row.get("payload"), Mapping) else {},
                "score_vector": dict(row.get("score_vector", {})) if isinstance(row.get("score_vector"), Mapping) else {},
            }
        )
    return out


def _unwrap_payload(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    if len(payload) == 1:
        only = next(iter(payload.values()))
        if isinstance(only, Mapping):
            return only
    return payload


def _lineage_state(envelopes: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    graph: dict[str, list[str]] = defaultdict(list)
    for envelope in envelopes:
        artifact_id = str(envelope.get("artifact_id") or "")
        parent_ids = [str(parent) for parent in envelope.get("parent_ids", []) if parent]
        payload = envelope.get("payload", {}) if isinstance(envelope.get("payload"), Mapping) else {}
        payload = _unwrap_payload(payload)
        routing = payload.get("routing", {}) if isinstance(payload.get("routing"), Mapping) else {}
        genome = payload.get("genome", {}) if isinstance(payload.get("genome"), Mapping) else {}
        metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata"), Mapping) else {}
        lineage_id = str(
            metadata.get("lineage_id")
            or routing.get("selected_domain")
            or genome.get("name")
            or (parent_ids[0] if parent_ids else artifact_id)
        )
        if lineage_id:
            counts[lineage_id] += 1
        graph.setdefault(artifact_id, [])
        for parent in parent_ids:
            graph[parent].append(artifact_id)
    total = sum(counts.values()) or 1
    dominant = max(counts.values(), default=0)
    return {
        "lineages": dict(counts),
        "graph": dict(graph),
        "surviving_lineages": len(counts),
        "lineage_concentration": round(dominant / total, 4),
    }


def _lineage_state_from_metrics(metrics: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    for row in metrics:
        routing = row.get("routing", {}) if isinstance(row.get("routing"), Mapping) else {}
        lineage_id = str(routing.get("selected_domain") or row.get("domain") or "default")
        counts[lineage_id] += 1
    total = sum(counts.values()) or 1
    dominant = max(counts.values(), default=0)
    return {
        "lineages": dict(counts),
        "graph": {},
        "surviving_lineages": len(counts),
        "lineage_concentration": round(dominant / total, 4),
    }


def _latest_mapping(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, Any]:
    for row in reversed(list(rows)):
        value = row.get(key)
        if isinstance(value, Mapping):
            return dict(value)
    return {}


def _archive_state() -> dict[str, Any]:
    archive_rows = _read_jsonl(_canonical_paths()["archive"])
    latest: dict[str, Any] = {}
    for row in archive_rows:
        kind = str(row.get("kind") or "")
        if kind:
            latest[kind] = row.get("payload")
    return latest


def _civilization_state(envelopes: Iterable[Mapping[str, Any]], archive_rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    artifact_counts: Counter[str] = Counter()
    lineage_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    policy_generations = 0
    memory_volume = 0
    for envelope in envelopes:
        artifact_type = str(envelope.get("artifact_type", envelope.get("type", "artifact")))
        if artifact_type == "domain":
            artifact_type = "domain_genome"
        artifact_counts[artifact_type or "artifact"] += 1
        payload = envelope.get("payload", {}) if isinstance(envelope.get("payload"), Mapping) else {}
        metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata"), Mapping) else {}
        parent_ids = [str(parent) for parent in envelope.get("parent_ids", []) if parent]
        artifact_id = str(envelope.get("artifact_id") or "")
        lineage_id = str(metadata.get("lineage_id") or (parent_ids[0] if parent_ids else artifact_id))
        if lineage_id:
            lineage_counts[lineage_id] += 1
        domain = str(
            payload.get("domain")
            or (payload.get("routing", {}) if isinstance(payload.get("routing"), Mapping) else {}).get("selected_domain")
            or "default"
        )
        domain_counts[domain] += 1
        if artifact_type == "policy":
            policy_generations += 1
    for row in archive_rows:
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


def _signal_state(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        sid = str(row.get("id") or "")
        if sid:
            latest[sid] = dict(row)
    status_counts: dict[str, int] = {}
    for row in latest.values():
        status = str(row.get("status") or "new")
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "signals": len(latest),
        "status_counts": status_counts,
        "queued": [row for row in latest.values() if str(row.get("status")) in {"new", "queued"}],
    }


def replay_state() -> dict[str, Any]:
    global _REPLAY_CACHE_KEY, _REPLAY_CACHE_VALUE
    paths = _canonical_paths()
    cache_key = tuple(sorted((name, *_path_signature(path)) for name, path in paths.items()))
    if _REPLAY_CACHE_KEY == cache_key and _REPLAY_CACHE_VALUE is not None:
        return dict(_REPLAY_CACHE_VALUE)
    events = _read_jsonl(paths["event_log"])
    metrics = _read_jsonl(paths["metrics"])
    archive_rows = _read_jsonl(paths["archive"])
    signals = _read_jsonl(paths["signals"])
    envelopes = _artifact_envelopes(_read_jsonl(paths["registry"]))
    archive_state = _archive_state()
    lineage_state = _lineage_state(envelopes) if envelopes else _lineage_state_from_metrics(metrics)
    last_metric = metrics[-1] if metrics else {}
    last_event = events[-1] if events else {}
    active_policies = archive_state.get("policy") if isinstance(archive_state.get("policy"), Mapping) else dict(last_metric.get("policy", {})) if isinstance(last_metric.get("policy"), Mapping) else {}
    quest_state = archive_state.get("quest") if isinstance(archive_state.get("quest"), Mapping) else dict(last_metric.get("quest", {})) if isinstance(last_metric.get("quest"), Mapping) else {}
    pressure_state = archive_state.get("stabilized_pressure") if isinstance(archive_state.get("stabilized_pressure"), Mapping) else _latest_mapping(metrics, "stabilized_pressure") or _latest_mapping(metrics, "pressure")
    pressure_state = {key: float(pressure_state.get(key, 0.0)) for key in CANONICAL_PRESSURE_KEYS}
    domain_routing_state = archive_state.get("routing") if isinstance(archive_state.get("routing"), Mapping) else dict(last_metric.get("routing", {})) if isinstance(last_metric.get("routing"), Mapping) else {}
    resource_allocation = archive_state.get("resource_allocation") if isinstance(archive_state.get("resource_allocation"), Mapping) else dict(last_metric.get("resource_allocation", {})) if isinstance(last_metric.get("resource_allocation"), Mapping) else {}
    exploration_economy_state = archive_state.get("exploration_economy_state") if isinstance(archive_state.get("exploration_economy_state"), Mapping) else dict(last_metric.get("exploration_economy_state", {})) if isinstance(last_metric.get("exploration_economy_state"), Mapping) else {}
    recovery_state = {
        "guard": archive_state.get("guard") if isinstance(archive_state.get("guard"), Mapping) else dict(last_metric.get("guard", {})) if isinstance(last_metric.get("guard"), Mapping) else {},
        "repair": archive_state.get("repair", last_metric.get("repair")),
        "supervisor_mode": str((last_event.get("payload", {}) if isinstance(last_event.get("payload"), Mapping) else {}).get("mode") or (last_metric.get("supervisor_mode") if isinstance(last_metric, Mapping) else "") or "normal"),
    }
    artifact_type_counts: Counter[str] = Counter(str(envelope.get("artifact_type", envelope.get("type", ""))) for envelope in envelopes)
    from federation.federation_replay import federation_replay_state

    payload = {
        "tick": int(last_metric.get("tick") or (last_event.get("payload", {}) if isinstance(last_event.get("payload"), Mapping) else {}).get("tick", 0) or 0),
        "events": len(events),
        "metrics": len(metrics),
        "artifacts": len(envelopes),
        "artifact_types": dict(artifact_type_counts),
        "active_policies": active_policies,
        "quest_state": quest_state,
        "lineage_state": lineage_state,
        "pressure_state": pressure_state,
        "domain_routing_state": domain_routing_state,
        "resource_allocation": resource_allocation,
        "exploration_economy_state": exploration_economy_state,
        "civilization_state": _civilization_state(envelopes, archive_rows),
        "recovery_state": recovery_state,
        "last_event": last_event,
        "last_metrics": last_metric,
        "archive_state": archive_state,
        "signals": len(signals),
        "signal_state": _signal_state(signals),
        "federation_replay": federation_replay_state(),
    }
    _REPLAY_CACHE_KEY = cache_key
    _REPLAY_CACHE_VALUE = dict(payload)
    return payload


def replay_state_hash() -> str:
    payload = replay_state()
    return json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


__all__ = ["CANONICAL_PRESSURE_KEYS", "replay_state", "replay_state_hash"]
