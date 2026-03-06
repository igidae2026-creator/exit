from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping

from core.log import AppendOnlyLogger


@dataclass(slots=True)
class ReplayState:
    events_seen: int = 0
    artifacts: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    quests: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    current_policies: Dict[str, str] = field(default_factory=dict)
    policy_history: List[Dict[str, Any]] = field(default_factory=list)
    metrics_history: List[Dict[str, float]] = field(default_factory=list)
    repairs: List[Dict[str, Any]] = field(default_factory=list)
    domain_genomes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    pressure_snapshots: List[Dict[str, float]] = field(default_factory=list)
    quota_decisions: List[Dict[str, Any]] = field(default_factory=list)
    supervisor_actions: List[Dict[str, Any]] = field(default_factory=list)
    tick_summaries: List[Dict[str, Any]] = field(default_factory=list)
    lineages: Dict[str, int] = field(default_factory=dict)

    def lineage_concentration(self) -> float:
        total = sum(self.lineages.values())
        if total <= 0:
            return 0.0
        return max(self.lineages.values()) / total


def rebuild_runtime_state(log_dir: str | Path = "data") -> ReplayState:
    logger = AppendOnlyLogger(log_dir=log_dir)
    state = ReplayState()

    for record in logger.replay_artifact_registry():
        state.events_seen += 1
        if record.event_type != "artifact_registered":
            continue
        payload = dict(record.payload)
        artifact_id = str(payload.get("artifact_id", ""))
        metadata = payload.get("metadata")
        if not artifact_id or not isinstance(metadata, dict):
            continue
        state.artifacts[artifact_id] = payload
        if metadata.get("artifact_type") == "strategy_genome":
            lineage_id = str(metadata.get("lineage_id") or "root")
            state.lineages[lineage_id] = state.lineages.get(lineage_id, 0) + 1

    for record in logger.replay_metrics():
        state.events_seen += 1
        if record.event_type != "metrics":
            continue
        state.metrics_history.append({k: float(v) for k, v in record.payload.items() if isinstance(v, (int, float))})

    for record in logger.replay_events():
        state.events_seen += 1
        payload = dict(record.payload)
        if record.event_type == "quest_proposed":
            quest = dict(payload.get("quest", {}))
            quest_id = str(quest.get("quest_id", ""))
            if quest_id:
                state.quests[quest_id] = quest
        elif record.event_type == "quest_selected":
            quest_id = str(payload.get("quest_id", ""))
            if quest_id and quest_id in state.quests:
                state.quests[quest_id]["state"] = "selected"
        elif record.event_type == "quest_retired":
            quest_id = str(payload.get("quest_id", ""))
            if quest_id and quest_id in state.quests:
                state.quests[quest_id]["state"] = "retired"
                state.quests[quest_id]["retired_reason"] = payload.get("reason")
        elif record.event_type in ("policy_registered", "policy_swapped"):
            state.policy_history.append(payload)
            policy_name = str(payload.get("policy_name", ""))
            artifact_id = str(payload.get("artifact_id", ""))
            if policy_name and artifact_id:
                state.current_policies[policy_name] = artifact_id
        elif record.event_type in ("repair_attempt", "repair_failed", "repair_succeeded"):
            state.repairs.append({"event_type": record.event_type, **payload})
        elif record.event_type == "domain_genome_loaded":
            adapter = str(payload.get("adapter", "canonical_domain"))
            state.domain_genomes[adapter] = payload
        elif record.event_type == "pressure_snapshot":
            state.pressure_snapshots.append({k: float(v) for k, v in payload.items() if isinstance(v, (int, float))})
        elif record.event_type == "quota_decision":
            state.quota_decisions.append(payload)
        elif record.event_type == "supervisor_action":
            state.supervisor_actions.append(payload)
        elif record.event_type == "tick_completed":
            state.tick_summaries.append(payload)

    return state


def archive_pressure(state: ReplayState, *, window: int = 5) -> Dict[str, float]:
    recent_metrics = state.metrics_history[-window:]
    novelty_values = [row.get("novelty", 0.0) for row in recent_metrics]
    diversity_values = [row.get("diversity", 0.0) for row in recent_metrics]

    novelty_avg = (sum(novelty_values) / len(novelty_values)) if novelty_values else 1.0
    diversity_avg = (sum(diversity_values) / len(diversity_values)) if diversity_values else 1.0
    recent_repairs = state.repairs[-window:]
    recent_failures = len([row for row in recent_repairs if row.get("event_type") == "repair_failed"])
    concentration = state.lineage_concentration()

    return {
        "exploration": round(max(0.0, 1.0 - novelty_avg), 6),
        "repair": round(min(1.0, recent_failures / max(1, window)), 6),
        "diversity": round(max(0.0, concentration - 0.45) + max(0.0, 0.45 - diversity_avg), 6),
        "replay": round(min(1.0, (len(state.tick_summaries[-window:]) / max(1, window)) * 0.5 + recent_failures * 0.1), 6),
        "collapse": round(max(0.0, concentration - 0.68), 6),
        "lineage_concentration": round(concentration, 6),
    }


__all__ = ["ReplayState", "archive_pressure", "rebuild_runtime_state"]
