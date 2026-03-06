from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.event_log import read_events, read_metrics
from core.registry import read_registry


@dataclass(slots=True)
class ReplayState:
    tick: int = 0
    best_score: float = float("-inf")
    latest_metrics: dict[str, float] = field(default_factory=dict)
    metric_history: list[dict[str, float]] = field(default_factory=list)
    quest_history: list[dict[str, Any]] = field(default_factory=list)
    active_quest: dict[str, Any] | None = None
    policies: list[dict[str, Any]] = field(default_factory=list)
    artifacts: dict[str, dict[str, Any]] = field(default_factory=dict)
    artifacts_by_kind: dict[str, int] = field(default_factory=dict)
    domain_history: list[str] = field(default_factory=list)
    supervisor_mode: str = "normal"
    retry_count: int = 0
    plateau_streak: int = 0
    last_error: str | None = None


def replay(data_dir: str = "data") -> list[dict[str, Any]]:
    return list(read_events(data_dir))


def replay_state(data_dir: str = "data") -> ReplayState:
    state = ReplayState()

    for row in read_registry(data_dir):
        artifact_id = str(row.get("artifact_id") or "")
        if not artifact_id:
            continue
        state.artifacts[artifact_id] = row
        kind = str(row.get("kind") or "unknown")
        state.artifacts_by_kind[kind] = state.artifacts_by_kind.get(kind, 0) + 1
        domain = str(row.get("domain") or "")
        if domain:
            state.domain_history.append(domain)
        score = row.get("score")
        if isinstance(score, (int, float)) and float(score) > state.best_score:
            state.best_score = float(score)
        tick = row.get("tick")
        if isinstance(tick, int):
            state.tick = max(state.tick, tick)

    for row in read_metrics(data_dir):
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        metric_row = {
            key: float(value)
            for key, value in payload.items()
            if isinstance(value, (int, float))
        }
        if metric_row:
            state.metric_history.append(metric_row)
            state.latest_metrics = metric_row
            score = metric_row.get("score")
            if score is not None:
                if score > state.best_score:
                    state.best_score = score
                    state.plateau_streak = 0
                else:
                    state.plateau_streak += 1
        tick = payload.get("tick")
        if isinstance(tick, int):
            state.tick = max(state.tick, tick)

    for row in read_events(data_dir):
        payload = row.get("payload", {})
        if not isinstance(payload, dict):
            continue
        event_type = str(row.get("event_type") or "")
        tick = payload.get("tick")
        if isinstance(tick, int):
            state.tick = max(state.tick, tick)
        if event_type in {"quest_selected", "quest_changed"}:
            quest = payload.get("quest")
            if isinstance(quest, dict):
                state.quest_history.append(quest)
                state.active_quest = quest
        elif event_type == "policy_evolved":
            policy = payload.get("policy")
            if isinstance(policy, dict):
                state.policies.append(policy)
        elif event_type == "supervisor_retry_once":
            state.retry_count += 1
            state.last_error = str(payload.get("error") or "retry")
        elif event_type == "safe_mode_entered":
            state.supervisor_mode = "safe_mode"
            state.last_error = str(payload.get("reason") or "safe_mode")
        elif event_type == "supervisor_checkpoint_restore":
            state.supervisor_mode = "checkpoint_restore"
        elif event_type == "quota_downshift":
            state.supervisor_mode = "quota_downshift"
        elif event_type == "cycle_completed":
            if payload.get("supervisor_mode"):
                state.supervisor_mode = str(payload["supervisor_mode"])
            score = payload.get("best_score")
            if isinstance(score, (int, float)):
                if float(score) > state.best_score:
                    state.best_score = float(score)
                    state.plateau_streak = 0
                else:
                    state.plateau_streak += 1

    if state.best_score == float("-inf"):
        state.best_score = 0.0
    return state
