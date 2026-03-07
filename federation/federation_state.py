from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any


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


def federation_state() -> dict[str, Any]:
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
    for row in rows:
        kind = str(row.get("kind", ""))
        payload = row.get("payload", {}) if isinstance(row.get("payload"), dict) else {}
        if kind == "artifact_exchange":
            artifact_id = str(payload.get("artifact_id", "")).strip()
            if artifact_id:
                shared_artifacts.append(artifact_id)
                artifact_flow += 1
        if kind == "domain_propagation":
            domain = str(payload.get("domain", "")).strip()
            if domain:
                shared_domains[domain] += 1
        if kind == "policy_diffusion":
            origin = str(payload.get("policy_origin", "")).strip() or "local"
            policy_diffusion[origin] += 1
        if kind == "knowledge_exchange":
            knowledge_propagation += 1
    return {
        "federation_enabled": federation_enabled(),
        "federation_nodes": nodes,
        "shared_artifacts": shared_artifacts[-128:],
        "shared_artifact_count": len(shared_artifacts),
        "shared_domains": sorted(shared_domains),
        "domain_propagation_rate": round(sum(shared_domains.values()) / max(1.0, float(len(rows) or 1)), 4),
        "policy_diffusion": dict(policy_diffusion),
        "knowledge_propagation": {
            "events": knowledge_propagation,
            "knowledge_exchange_events": knowledge_propagation,
        },
        "artifact_exchange_rate": round(artifact_flow / max(1.0, float(len(rows) or 1)), 4),
    }


__all__ = [
    "append_federation_row",
    "federation_enabled",
    "federation_state",
    "local_node_id",
]
