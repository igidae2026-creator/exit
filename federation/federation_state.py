from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from federation.federation_topology import topology_state
from federation.federation_transport import transport_state

_FEDERATION_CACHE_KEY: tuple[str, bool, int, int] | None = None
_FEDERATION_CACHE_VALUE: dict[str, Any] | None = None

def _root() -> Path:
    root = os.environ.get("METAOS_ROOT")
    return Path(root) if root else Path(".metaos_runtime")


def _federation_dir() -> Path:
    path = _root() / "federation"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _path(name: str) -> Path:
    return _federation_dir() / name


def federation_enabled() -> bool:
    return os.environ.get("METAOS_FEDERATION_ENABLED", "0") in {"1", "true", "yes"}


def local_node_id() -> str:
    return str(os.environ.get("METAOS_NODE_ID") or _root().name or "local")


def append_federation_row(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    row = {
        "kind": str(kind),
        "node_id": local_node_id(),
        "payload": dict(payload),
    }
    path = _path("events.jsonl")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    return row


def _rows() -> list[dict[str, Any]]:
    path = _path("events.jsonl")
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                out.append(row)
    return out


def _event_signature() -> tuple[str, bool, int, int]:
    path = _path("events.jsonl")
    if not path.exists():
        return (str(path), False, 0, 0)
    stat = path.stat()
    return (str(path), True, int(stat.st_size), int(stat.st_mtime_ns))


def federation_state() -> dict[str, Any]:
    global _FEDERATION_CACHE_KEY, _FEDERATION_CACHE_VALUE
    path = _path("events.jsonl")
    if not federation_enabled() and not path.exists():
        topology = topology_state([local_node_id()], "peer", artifact_events=0, knowledge_events=0)
        payload = {
            "federation_enabled": False,
            "federation_nodes": [local_node_id()],
            "shared_artifacts": [],
            "shared_artifact_count": 0,
            "shared_domains": [],
            "shared_domain_count": 0,
            "domain_propagation_rate": 0.0,
            "policy_diffusion_count": 0,
            "policy_diffusion_rate": 0.0,
            "policy_diffusion": {},
            "knowledge_propagation": {"events": 0, "knowledge_exchange_events": 0},
            "knowledge_flow_rate": 0.0,
            "artifact_exchange_rate": 0.0,
            "node_topology": topology,
            "federation_topology": topology,
            "knowledge_import_count": 0,
            "knowledge_export_count": 0,
            "observed_external_artifacts": 0,
            "imported_external_artifacts": 0,
            "adopted_external_artifacts": 0,
            "active_external_artifacts": 0,
            "imported_domains": 0,
            "adopted_domains": 0,
            "active_imported_domains": 0,
            "observed_external_policies": 0,
            "adopted_external_policies": 0,
            "active_external_policies": 0,
            "imported_evaluation_generations": 0,
            "adopted_evaluation_generations": 0,
            "active_external_evaluation_generations": 0,
            "mirrored_external_artifacts": 0,
            "active_mirrored_artifacts": 0,
            "hydration_rate": 0.0,
            "hydration_depth_distribution": {},
            "foreign_origin_distribution": {},
            "mirror_lineage_count": 0,
            "federation_adoption_rate": 0.0,
            "federation_activation_rate": 0.0,
            "federation_influence_score": 0.0,
            "send_queue_depth": 0,
            "receive_queue_depth": 0,
            "adoption_queue_depth": 0,
            "transport_delivery_rate": 0.0,
            "adoption_completion_rate": 0.0,
            "federation_monoculture_score": 0.0,
        }
        _FEDERATION_CACHE_KEY = _event_signature()
        _FEDERATION_CACHE_VALUE = dict(payload)
        return payload
    cache_key = _event_signature()
    if _FEDERATION_CACHE_KEY == cache_key and _FEDERATION_CACHE_VALUE is not None:
        return dict(_FEDERATION_CACHE_VALUE)
    rows = _rows()
    nodes = sorted(
        {
            str(row.get("node_id", "")).strip()
            for row in rows
            if str(row.get("node_id", "")).strip()
        }
        | {local_node_id()}
    )
    shared_artifacts: list[str] = []
    shared_domains: Counter[str] = Counter()
    policy_diffusion: Counter[str] = Counter()
    knowledge_propagation = 0
    artifact_flow = 0
    domain_flow = 0
    policy_flow = 0
    adoption_counts: Counter[str] = Counter()
    origin_counts: Counter[str] = Counter()
    for row in rows:
        kind = str(row.get("kind", ""))
        payload = row.get("payload", {}) if isinstance(row.get("payload"), dict) else {}
        if kind == "artifact_exchange":
            artifact_id = str(payload.get("artifact_id", "")).strip()
            if artifact_id:
                shared_artifacts.append(artifact_id)
                artifact_flow += 1
                origin_counts[str(payload.get("artifact_origin", row.get("node_id", "")))] += 1
        if kind == "domain_propagation":
            domain = str(payload.get("domain", "")).strip()
            if domain:
                shared_domains[domain] += 1
                domain_flow += 1
                origin_counts[str(payload.get("domain_origin", row.get("node_id", "")))] += 1
        if kind == "policy_diffusion":
            origin = str(payload.get("policy_origin", "")).strip() or "local"
            policy_diffusion[origin] += 1
            policy_flow += 1
            origin_counts[origin] += 1
        if kind == "knowledge_exchange":
            knowledge_propagation += 1
        if kind.endswith("_adoption"):
            base = kind.replace("_adoption", "")
            status = str(payload.get("status", "observed"))
            adoption_counts[f"{base}:{status}"] += 1
    topology_name = str(os.environ.get("METAOS_FEDERATION_TOPOLOGY", "peer"))
    topology = topology_state(nodes, topology_name, artifact_events=artifact_flow, knowledge_events=knowledge_propagation)
    transport = transport_state(rows)
    hydration_rows = [row.get("payload", {}) for row in rows if str(row.get("kind", "")) == "artifact_hydration" and isinstance(row.get("payload"), dict)]
    dominant_origin_share = max(origin_counts.values(), default=0) / max(1.0, float(sum(origin_counts.values()) or 1))
    federation_adoption_rate = round(
        (
            adoption_counts.get("artifact:adopted", 0)
            + adoption_counts.get("domain:adopted", 0)
            + adoption_counts.get("policy:adopted", 0)
            + adoption_counts.get("evaluation:adopted", 0)
        )
        / max(1.0, float(len(rows) or 1)),
        4,
    )
    federation_activation_rate = round(
        (
            adoption_counts.get("artifact:activated", 0)
            + adoption_counts.get("domain:activated", 0)
            + adoption_counts.get("policy:activated", 0)
            + adoption_counts.get("evaluation:activated", 0)
        )
        / max(1.0, float(len(rows) or 1)),
        4,
    )
    federation_influence_score = round(
        max(
            0.0,
            min(
                1.0,
                (0.35 * federation_adoption_rate)
                + (0.35 * federation_activation_rate)
                + (0.15 * float(transport.get("transport_delivery_rate", 0.0)))
                + (0.15 * float(transport.get("adoption_completion_rate", 0.0))),
            ),
        ),
        4,
    )
    mirrored_external_artifacts = len({str(row.get("artifact_id", "")) for row in hydration_rows if row.get("artifact_id")})
    active_mirrored_artifacts = len({str(row.get("artifact_id", "")) for row in hydration_rows if bool(row.get("hydrated"))})
    hydration_depth_distribution: Counter[int] = Counter(int(row.get("hydration_depth", 0) or 0) for row in hydration_rows)
    foreign_origin_distribution: Counter[str] = Counter(str(row.get("origin_node", "")) for row in hydration_rows if row.get("origin_node"))
    mirror_lineage_count = len({tuple(row.get("mirror_parent_ids", [])) for row in hydration_rows if row.get("mirror_parent_ids")})
    total_hydration = sum(hydration_depth_distribution.values()) or 1
    hydration_rate = round(mirrored_external_artifacts / max(1.0, float(adoption_counts.get("artifact:adopted", 0) or 1)), 4)
    payload = {
        "federation_enabled": federation_enabled(),
        "federation_nodes": nodes,
        "shared_artifacts": shared_artifacts[-128:],
        "shared_artifact_count": len(shared_artifacts),
        "shared_domains": sorted(shared_domains),
        "shared_domain_count": len(shared_domains),
        "domain_propagation_rate": round(sum(shared_domains.values()) / max(1.0, float(len(rows) or 1)), 4),
        "policy_diffusion_count": sum(policy_diffusion.values()),
        "policy_diffusion_rate": round(policy_flow / max(1.0, float(len(rows) or 1)), 4),
        "policy_diffusion": dict(policy_diffusion),
        "knowledge_propagation": {
            "events": knowledge_propagation,
            "knowledge_exchange_events": knowledge_propagation,
        },
        "knowledge_flow_rate": round(knowledge_propagation / max(1.0, float(len(rows) or 1)), 4),
        "artifact_exchange_rate": round(artifact_flow / max(1.0, float(len(rows) or 1)), 4),
        "node_topology": topology,
        "federation_topology": topology,
        "knowledge_import_count": knowledge_propagation,
        "knowledge_export_count": knowledge_propagation,
        "observed_external_artifacts": adoption_counts.get("artifact:observed", 0),
        "imported_external_artifacts": adoption_counts.get("artifact:imported", 0),
        "adopted_external_artifacts": adoption_counts.get("artifact:adopted", 0),
        "active_external_artifacts": adoption_counts.get("artifact:activated", 0),
        "imported_domains": adoption_counts.get("domain:imported", 0),
        "adopted_domains": adoption_counts.get("domain:adopted", 0),
        "active_imported_domains": adoption_counts.get("domain:activated", 0),
        "observed_external_policies": adoption_counts.get("policy:observed", 0),
        "adopted_external_policies": adoption_counts.get("policy:adopted", 0),
        "active_external_policies": adoption_counts.get("policy:activated", 0),
        "imported_evaluation_generations": adoption_counts.get("evaluation:imported", 0),
        "adopted_evaluation_generations": adoption_counts.get("evaluation:adopted", 0),
        "active_external_evaluation_generations": adoption_counts.get("evaluation:activated", 0),
        "mirrored_external_artifacts": mirrored_external_artifacts,
        "active_mirrored_artifacts": active_mirrored_artifacts,
        "hydration_rate": hydration_rate,
        "hydration_depth_distribution": {str(key): round(value / total_hydration, 4) for key, value in sorted(hydration_depth_distribution.items())},
        "foreign_origin_distribution": dict(foreign_origin_distribution),
        "mirror_lineage_count": mirror_lineage_count,
        "federation_adoption_rate": federation_adoption_rate,
        "federation_activation_rate": federation_activation_rate,
        "federation_influence_score": federation_influence_score,
        "send_queue_depth": int(transport.get("send_queue_depth", 0)),
        "receive_queue_depth": int(transport.get("receive_queue_depth", 0)),
        "adoption_queue_depth": int(transport.get("adoption_queue_depth", 0)),
        "transport_delivery_rate": float(transport.get("transport_delivery_rate", 0.0)),
        "adoption_completion_rate": float(transport.get("adoption_completion_rate", 0.0)),
        "federation_monoculture_score": round(dominant_origin_share, 4),
    }
    _FEDERATION_CACHE_KEY = cache_key
    _FEDERATION_CACHE_VALUE = dict(payload)
    return payload


__all__ = [
    "append_federation_row",
    "federation_enabled",
    "federation_state",
    "local_node_id",
]
