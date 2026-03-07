from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
from typing import Any

from genesis.replay import replay_state
from runtime.civilization_state import civilization_state


def _pattern_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        payload = row.get(key, {}) if isinstance(row.get(key), dict) else {}
        if payload:
            counts[str(sorted(payload.items()))] += 1
    return dict(counts)


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [dict(item) for item in value] if isinstance(value, list) else []


def _replay_reference_counts(state: Any) -> dict[str, int]:
    if isinstance(state, Mapping):
        return {
            "artifacts": int(state.get("artifacts", 0)),
            "metrics": int(state.get("metrics", 0)),
            "events": int(state.get("events", 0)),
        }
    artifacts = getattr(state, "artifacts", {}) or {}
    metric_history = getattr(state, "metric_history", []) or []
    tick_summaries = getattr(state, "tick_summaries", []) or []
    return {
        "artifacts": len(artifacts) if isinstance(artifacts, Mapping) else 0,
        "metrics": len(metric_history) if isinstance(metric_history, list) else 0,
        "events": len(tick_summaries) if isinstance(tick_summaries, list) else 0,
    }


def accumulated_knowledge(*, replay: Any | None = None, civilization: Mapping[str, Any] | None = None) -> dict[str, Any]:
    state = replay if replay is not None else replay_state()
    civilization_payload = (
        dict(civilization)
        if civilization is not None
        else ({} if replay is not None else civilization_state())
    )
    state_map = _mapping(state)
    if state_map:
        archive_rows = list(_mapping(state_map.get("archive_state", {})).items())
        artifacts = [dict(value) for value in _mapping(state_map.get("artifacts", {})).values()]
        lineage_graph = dict(_mapping(_mapping(state_map.get("lineage_state", {})).get("graph", {})))
        metrics_history = _list_of_dicts(state_map.get("metric_history"))
    else:
        archive_rows = []
        artifacts = [dict(value) for value in (_mapping(getattr(state, "artifacts", {}))).values()]
        lineage_graph = dict(getattr(state, "lineage_graph", {}) or {})
        metrics_history = [dict(item) for item in (getattr(state, "metric_history", []) or []) if isinstance(item, Mapping)]
    archive_kinds = [str(kind) for kind, _ in archive_rows]
    artifact_memory_graph: dict[str, list[str]] = defaultdict(list)
    lineage_ancestry_graph: dict[str, list[str]] = defaultdict(list)
    domain_knowledge: dict[str, dict[str, Any]] = defaultdict(lambda: {"artifacts": 0, "patterns": Counter(), "lineages": set()})
    for artifact in artifacts:
        artifact_id = str(artifact.get("artifact_id", ""))
        parents = [str(parent) for parent in artifact.get("parent_ids", []) if parent]
        domain = str(artifact.get("domain") or ((artifact.get("payload") or {}) if isinstance(artifact.get("payload"), dict) else {}).get("domain") or "unknown")
        lineage_id = str(artifact.get("lineage_id") or artifact_id)
        artifact_memory_graph[artifact_id].extend(parents)
        lineage_ancestry_graph[lineage_id].extend(parents)
        domain_knowledge[domain]["artifacts"] += 1
        domain_knowledge[domain]["lineages"].add(lineage_id)
        artifact_type = str(artifact.get("artifact_type", artifact.get("type", "")))
        if artifact_type:
            domain_knowledge[domain]["patterns"][artifact_type] += 1
    return {
        "artifact_archives": archive_kinds,
        "lineage_graph": lineage_graph,
        "artifact_memory_graph": {key: list(dict.fromkeys(values)) for key, values in artifact_memory_graph.items()},
        "lineage_ancestry_graph": {key: list(dict.fromkeys(values)) for key, values in lineage_ancestry_graph.items()},
        "pattern_library": {
            "strategy_patterns": _pattern_counts(metrics_history, "strategy"),
            "policy_patterns": _pattern_counts(metrics_history, "policy"),
            "evaluation_patterns": _pattern_counts(metrics_history, "evaluation"),
        },
        "domain_knowledge": {
            domain: {
                "artifact_count": value["artifacts"],
                "lineage_count": len(value["lineages"]),
                "top_patterns": dict(value["patterns"].most_common(6)),
            }
            for domain, value in domain_knowledge.items()
        },
        "civilization_memory": civilization_payload,
        "references": _replay_reference_counts(state),
    }


def knowledge_guidance(
    *,
    domain: str,
    pressure: dict[str, Any] | None = None,
) -> dict[str, Any]:
    knowledge = accumulated_knowledge()
    domain_state = dict((knowledge.get("domain_knowledge", {}) if isinstance(knowledge.get("domain_knowledge"), dict) else {}).get(domain, {}))
    pressure_state = dict(pressure or {})
    top_patterns = list(domain_state.get("top_patterns", {}))
    return {
        "domain": domain,
        "top_pattern_hints": top_patterns[:3],
        "reusable_pattern_count": len(top_patterns),
        "ancestry_density": round(
            len((knowledge.get("lineage_ancestry_graph", {}) if isinstance(knowledge.get("lineage_ancestry_graph"), dict) else {}))
            / max(1.0, float(knowledge.get("references", {}).get("artifacts", 1))),
            4,
        ),
        "reuse_bias": round(
            min(
                1.0,
                0.20
                + (0.10 * len(top_patterns))
                + (0.25 * float(pressure_state.get("resurrection_potential", 0.0)))
                + (0.20 * float(pressure_state.get("innovation_density", 0.0))),
            ),
            4,
        ),
    }


__all__ = ["accumulated_knowledge", "knowledge_guidance"]
