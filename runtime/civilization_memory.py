from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from collections import Counter

from artifact.archive import append_archive, archive_window, latest_archive, load_archive
from artifact.civilization_registry import civilization_memory_snapshot as artifact_civilization_memory_snapshot
from artifact.civilization_registry import civilization_state as artifact_civilization_state
from federation.federation_state import federation_state


def _memory_path() -> Path:
    root = os.environ.get("METAOS_ROOT")
    if os.environ.get("METAOS_CIVILIZATION_MEMORY"):
        return Path(os.environ["METAOS_CIVILIZATION_MEMORY"])
    if root:
        return Path(root) / "archive" / "civilization_memory.jsonl"
    return Path(".metaos_runtime/archive/civilization_memory.jsonl")


def _memory_rows() -> list[dict[str, Any]]:
    path = _memory_path()
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _metrics_path() -> Path:
    root = os.environ.get("METAOS_ROOT")
    if os.environ.get("METAOS_METRICS"):
        return Path(os.environ["METAOS_METRICS"])
    if root:
        return Path(root) / "metrics.jsonl"
    return Path(".metaos_runtime/data/metrics.jsonl")


def _metrics_rows() -> list[dict[str, Any]]:
    path = _metrics_path()
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def metrics_window(limit: int = 64) -> list[dict[str, Any]]:
    return _metrics_rows()[-max(1, int(limit)) :]


def _policy_generations_from_metrics(rows: list[dict[str, Any]]) -> int:
    seen: set[str] = set()
    for row in rows:
        policy = row.get("policy", {}) if isinstance(row.get("policy"), dict) else {}
        if policy:
            seen.add(json.dumps(policy, sort_keys=True, ensure_ascii=True))
    return len(seen)


def _evaluation_generations_from_metrics(rows: list[dict[str, Any]]) -> int:
    seen: set[str] = set()
    for row in rows:
        evaluation = row.get("evaluation", {}) if isinstance(row.get("evaluation"), dict) else {}
        if evaluation:
            seen.add(json.dumps(evaluation, sort_keys=True, ensure_ascii=True))
    return len(seen)


def _evaluation_generations_from_memory(rows: list[dict[str, Any]]) -> int:
    seen: set[str] = set()
    for row in rows:
        if str(row.get("kind", "")) != "evaluation_artifact":
            continue
        payload = row.get("payload", {}) if isinstance(row.get("payload"), dict) else {}
        evaluation = payload.get("evaluation", {}) if isinstance(payload.get("evaluation"), dict) else {}
        if evaluation:
            seen.add(json.dumps(evaluation, sort_keys=True, ensure_ascii=True))
    return len(seen)


def _active_evaluation_distribution_from_memory(rows: list[dict[str, Any]]) -> dict[str, float]:
    counts: Counter[str] = Counter()
    for row in rows[-32:]:
        if str(row.get("kind", "")) != "evaluation_artifact":
            continue
        payload = row.get("payload", {}) if isinstance(row.get("payload"), dict) else {}
        evaluation = payload.get("evaluation", {}) if isinstance(payload.get("evaluation"), dict) else {}
        regime = str(evaluation.get("regime", payload.get("evaluation_regime", ""))).strip()
        if regime:
            counts[regime] += 1
    total = sum(counts.values()) or 1
    return {key: round(value / total, 4) for key, value in sorted(counts.items())}


def _domain_counts_from_runtime(metrics_rows: list[dict[str, Any]], memory_rows: list[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in metrics_rows:
        routing = row.get("routing", {}) if isinstance(row.get("routing"), dict) else {}
        domain = str(routing.get("selected_domain") or row.get("domain") or "").strip()
        if domain:
            counts[domain] += 1
    for row in memory_rows:
        payload = row.get("payload", {}) if isinstance(row.get("payload"), dict) else {}
        domain_creation = payload.get("domain_creation", {}) if isinstance(payload.get("domain_creation"), dict) else {}
        name = str(payload.get("name") or domain_creation.get("name") or "").strip()
        if name:
            counts.setdefault(name, 0)
    return counts


def civilization_state() -> dict[str, Any]:
    archive_rows = load_archive()
    memory_rows = _memory_rows()
    metrics_rows = _metrics_rows()
    if os.environ.get("METAOS_ROOT") or os.environ.get("METAOS_REGISTRY"):
        artifact_state = artifact_civilization_state()
    else:
        artifact_state = {
            "artifact_counts": {},
            "domain_counts": {},
            "lineage_counts": {},
            "policy_generations": 0,
        }
    artifact_distribution = dict(artifact_state.get("artifact_distribution", artifact_state.get("artifact_counts", {})))
    domain_counts = Counter(
        {
            str(key): int(round(float(value) * 1000)) if isinstance(value, float) and value <= 1.0 else int(value)
            for key, value in dict(artifact_state.get("domain_counts", artifact_state.get("domain_distribution", {}))).items()
        }
    )
    domain_counts.update(_domain_counts_from_runtime(metrics_rows, memory_rows))
    total_domains = sum(domain_counts.values()) or 1
    domain_distribution = {key: round(value / total_domains, 4) for key, value in sorted(domain_counts.items())}
    active_domains = sorted(name for name, value in domain_counts.items() if int(value) > 0)
    inactive_domains = sorted(name for name, value in domain_counts.items() if int(value) <= 0)
    active_total = sum(int(domain_counts.get(name, 0)) for name in active_domains) or 1
    active_domain_distribution = {
        name: round(int(domain_counts.get(name, 0)) / active_total, 4)
        for name in active_domains
    }
    lineage_counts = dict(artifact_state.get("lineage_counts", {}))
    archive_kinds = {str(row.get("kind", "")) for row in archive_rows if row.get("kind")}
    memory_kinds = {str(row.get("kind", "")) for row in memory_rows if row.get("kind")}
    density_base = len(archive_kinds | memory_kinds) + len(domain_distribution) + len(artifact_distribution) + len(lineage_counts)
    total_rows = len(archive_rows) + len(memory_rows)
    policy_generations = max(int(artifact_state.get("policy_generations", 0)), _policy_generations_from_metrics(metrics_rows))
    evaluation_generations = max(
        int(artifact_state.get("evaluation_generations", 0)),
        _evaluation_generations_from_metrics(metrics_rows),
        _evaluation_generations_from_memory(memory_rows),
    )
    active_evaluation_distribution = _active_evaluation_distribution_from_memory(memory_rows)
    federation = federation_state()
    knowledge_density = round(max(float(artifact_state.get("knowledge_density", 0.0)), min(1.0, density_base / 24.0)), 4)
    memory_growth = round(max(float(artifact_state.get("memory_growth", 0.0)), min(1.0, total_rows / 720.0)), 4)
    return {
        "knowledge_density": knowledge_density,
        "memory_growth": memory_growth,
        "artifact_distribution": artifact_distribution,
        "domain_distribution": domain_distribution,
        "active_domain_distribution": active_domain_distribution,
        "policy_generations": policy_generations,
        "evaluation_generations": evaluation_generations,
        "active_evaluation_distribution": active_evaluation_distribution,
        "active_evaluation_generations": len(active_evaluation_distribution),
        "knowledge_exchange_events": int((federation.get("knowledge_propagation", {}) if isinstance(federation.get("knowledge_propagation"), dict) else {}).get("knowledge_exchange_events", 0)),
        "federation_memory_growth": round(min(1.0, float((federation.get("knowledge_propagation", {}) if isinstance(federation.get("knowledge_propagation"), dict) else {}).get("knowledge_exchange_events", 0)) / 128.0), 4),
        "lineage_counts": lineage_counts,
        "created_domains": sorted(domain_counts),
        "active_domains": active_domains,
        "inactive_domains": inactive_domains,
        "created_domain_count": len(domain_counts),
        "active_domain_count": len(active_domains),
        "exploration_outcomes": {
            "archived_rows": len(archive_rows),
            "memory_rows": len(memory_rows),
            "outcome_kinds": sorted(kind for kind in archive_kinds if kind),
        },
    }


def remember(kind: str, payload: Any) -> dict[str, Any]:
    row = {"kind": str(kind), "payload": payload}
    path = _memory_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    append_archive("memory", row)
    return row


def memory_window(limit: int = 64) -> list[dict[str, Any]]:
    return _memory_rows()[-max(1, int(limit)) :]


def latest_memory(kind: str, default: Any = None) -> Any:
    target = str(kind)
    for row in reversed(_memory_rows()):
        if str(row.get("kind", "")) == target:
            return row.get("payload")
    archive_default = latest_archive(target, default)
    return archive_default


def civilization_memory_snapshot() -> dict[str, Any]:
    snapshot = artifact_civilization_memory_snapshot()
    state = civilization_state()
    snapshot.update(
        {
            "artifact_distribution": dict(state.get("artifact_distribution", snapshot.get("artifact_distribution", {}))),
            "domain_distribution": dict(state.get("domain_distribution", snapshot.get("domain_distribution", {}))),
            "active_domain_distribution": dict(state.get("active_domain_distribution", {})),
            "policy_generations": int(state.get("policy_generations", snapshot.get("policy_generations", 0))),
            "evaluation_generations": int(state.get("evaluation_generations", snapshot.get("evaluation_generations", 0))),
            "active_evaluation_distribution": dict(state.get("active_evaluation_distribution", {})),
            "active_evaluation_generations": int(state.get("active_evaluation_generations", 0)),
            "knowledge_exchange_events": int(state.get("knowledge_exchange_events", 0)),
            "federation_memory_growth": float(state.get("federation_memory_growth", 0.0)),
            "lineage_counts": dict(state.get("lineage_counts", snapshot.get("lineage_counts", {}))),
            "created_domains": list(state.get("created_domains", [])),
            "active_domains": list(state.get("active_domains", [])),
            "inactive_domains": list(state.get("inactive_domains", [])),
            "created_domain_count": int(state.get("created_domain_count", 0)),
            "active_domain_count": int(state.get("active_domain_count", 0)),
            "memory_growth": float(state.get("memory_growth", snapshot.get("memory_growth", 0.0))),
            "knowledge_density": float(state.get("knowledge_density", snapshot.get("knowledge_density", 0.0))),
        }
    )
    return snapshot


__all__ = [
    "civilization_memory_snapshot",
    "civilization_state",
    "latest_memory",
    "metrics_window",
    "memory_window",
    "remember",
]
