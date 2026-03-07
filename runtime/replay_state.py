from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List

from artifact.lineage import lineage_counts as replay_lineage_counts, lineage_graph
from genesis.event_log import ensure_spine, read_events, read_metrics, read_registry
from domains.domain_genome import canonical_domain_genome, domain_plugin_names


@dataclass(slots=True)
class ReplayState:
    data_dir: str = "data"
    state_dir: str = "state"
    archive_dir: str = "archive"
    tick: int = 0
    best_score: float = 0.0
    events_seen: int = 0
    artifacts: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    artifacts_by_kind: Dict[str, int] = field(default_factory=dict)
    policies: List[Dict[str, Any]] = field(default_factory=list)
    current_policies: Dict[str, str] = field(default_factory=dict)
    policy_history: List[Dict[str, Any]] = field(default_factory=list)
    quests: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    active_quest: Dict[str, Any] | None = None
    quest_portfolio: List[Dict[str, Any]] = field(default_factory=list)
    metric_history: List[Dict[str, float]] = field(default_factory=list)
    latest_metrics: Dict[str, float] = field(default_factory=dict)
    repairs: List[Dict[str, Any]] = field(default_factory=list)
    domain_genomes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    domain_counts: Dict[str, int] = field(default_factory=dict)
    pressure_snapshots: List[Dict[str, float]] = field(default_factory=list)
    quota_decisions: List[Dict[str, Any]] = field(default_factory=list)
    supervisor_actions: List[Dict[str, Any]] = field(default_factory=list)
    tick_summaries: List[Dict[str, Any]] = field(default_factory=list)
    lineages: Dict[str, int] = field(default_factory=dict)
    lineage_graph: Dict[str, List[str]] = field(default_factory=dict)
    checkpoint: Dict[str, Any] = field(default_factory=dict)
    supervisor_mode: str = "normal"
    plateau_streak: int = 0
    retry_count: int = 0
    archive: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)

    def lineage_concentration(self) -> float:
        total = sum(self.lineages.values())
        if total <= 0:
            return 0.0
        return max(self.lineages.values()) / total


ARCHIVE_FILES = {
    "artifacts": "artifacts.jsonl",
    "policies": "policies.jsonl",
    "pressure_snapshots": "pressure_snapshots.jsonl",
    "quests": "quests.jsonl",
    "quota_decisions": "quota_decisions.jsonl",
    "domain_genomes": "domain_genomes.jsonl",
}


def _read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
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


def _load_checkpoint(state_dir: str | Path = "state") -> dict[str, Any]:
    path = Path(state_dir) / "checkpoint.json"
    if not path.exists():
        return {}
    try:
        row = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return row if isinstance(row, dict) else {}


def replay_state(data_dir: str | Path = "data", *, state_dir: str | Path = "state", archive_dir: str | Path = "archive") -> ReplayState:
    ensure_spine(data_dir)
    state = ReplayState(data_dir=str(data_dir), state_dir=str(state_dir), archive_dir=str(archive_dir))
    state.checkpoint = _load_checkpoint(state_dir)
    state.tick = int(state.checkpoint.get("tick", 0) or 0)
    state.best_score = float(state.checkpoint.get("best_score", 0.0) or 0.0)

    for row in read_registry(data_dir):
        state.events_seen += 1
        artifact_id = str(row.get("artifact_id") or "")
        if not artifact_id:
            continue
        payload = dict(row)
        state.artifacts[artifact_id] = payload
        kind = str(payload.get("kind") or payload.get("metadata", {}).get("artifact_type") or "artifact")
        state.artifacts_by_kind[kind] = state.artifacts_by_kind.get(kind, 0) + 1
        domain = str(payload.get("domain") or payload.get("metadata", {}).get("domain") or "unknown")
        state.domain_counts[domain] = state.domain_counts.get(domain, 0) + 1

    for row in read_metrics(data_dir):
        state.events_seen += 1
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        metric_row = {key: float(value) for key, value in payload.items() if isinstance(value, (int, float))}
        if metric_row:
            state.metric_history.append(metric_row)
            state.latest_metrics = metric_row
            state.best_score = max(state.best_score, float(metric_row.get("score", 0.0)))
            state.tick = max(state.tick, int(metric_row.get("tick", state.tick) or state.tick))

    prior_best = None
    streak = 0
    for row in state.metric_history:
        current = float(row.get("score", 0.0))
        if prior_best is not None and current <= prior_best + 0.0001:
            streak += 1
        else:
            streak = 0
            prior_best = max(prior_best or 0.0, current)
    state.plateau_streak = streak

    for row in read_events(data_dir):
        state.events_seen += 1
        event_type = str(row.get("event_type") or "")
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        if event_type in {"tick_completed", "cycle_completed"}:
            state.tick_summaries.append(dict(payload))
            state.tick = max(state.tick, int(payload.get("tick", state.tick) or state.tick))
            state.best_score = max(state.best_score, float(payload.get("best_score", state.best_score) or state.best_score))
            state.supervisor_mode = str(payload.get("supervisor_mode", state.supervisor_mode) or state.supervisor_mode)
        elif event_type in {"quest_proposed", "quest_selected", "quest_retired"}:
            quest = payload.get("quest") if isinstance(payload.get("quest"), dict) else {}
            quest_id = str(payload.get("quest_id") or quest.get("quest_id") or quest.get("id") or "")
            if quest_id:
                current = dict(state.quests.get(quest_id, {}))
                current.update(dict(quest))
                if event_type == "quest_selected":
                    current["state"] = "selected"
                    state.active_quest = current
                elif event_type == "quest_retired":
                    current["state"] = "retired"
                else:
                    current.setdefault("state", "proposed")
                state.quests[quest_id] = current
        elif event_type in {"policy_registered", "policy_swapped", "policy_snapshot"}:
            state.policy_history.append(dict(payload))
            state.policies.append(dict(payload))
            policy_name = str(payload.get("policy_name") or payload.get("name") or "")
            artifact_id = str(payload.get("artifact_id") or "")
            if policy_name and artifact_id:
                state.current_policies[policy_name] = artifact_id
        elif event_type in {"repair_attempt", "repair_failed", "repair_succeeded"}:
            state.repairs.append({"event_type": event_type, **dict(payload)})
            if event_type == "repair_failed":
                state.retry_count += 1
        elif event_type == "pressure_snapshot":
            state.pressure_snapshots.append({k: float(v) for k, v in payload.items() if isinstance(v, (int, float))})
        elif event_type == "quota_decision":
            state.quota_decisions.append(dict(payload))
        elif event_type == "supervisor_action":
            state.supervisor_actions.append(dict(payload))
            state.supervisor_mode = str(payload.get("mode") or payload.get("hook") or state.supervisor_mode)
        elif event_type == "domain_genome_loaded":
            adapter = str(payload.get("adapter") or "unknown")
            state.domain_genomes[adapter] = dict(payload)
        elif event_type == "quest_portfolio":
            portfolio = payload.get("quests") if isinstance(payload.get("quests"), list) else []
            state.quest_portfolio = [dict(item) for item in portfolio if isinstance(item, dict)]

    archive_root = Path(archive_dir)
    for key, filename in ARCHIVE_FILES.items():
        state.archive[key] = list(_read_jsonl(archive_root / filename))
        if key == "domain_genomes":
            for row in state.archive[key]:
                adapter = str(row.get("adapter") or "unknown")
                state.domain_genomes[adapter] = dict(row)

    if not state.quest_portfolio:
        state.quest_portfolio = [quest for quest in state.quests.values() if quest.get("state") != "retired"]
    if state.active_quest is None and state.quest_portfolio:
        state.active_quest = dict(state.quest_portfolio[0])
    state.lineages = replay_lineage_counts(str(data_dir))
    state.lineage_graph = lineage_graph(str(data_dir))
    if not state.domain_genomes:
        for domain_name in domain_plugin_names():
            state.domain_genomes[domain_name] = canonical_domain_genome(domain_name).to_dict()
    elif "code_domain" not in state.domain_genomes:
        state.domain_genomes["code_domain"] = canonical_domain_genome("code_domain").to_dict()
    if not state.domain_counts:
        state.domain_counts["code_domain"] = 0
    if state.active_quest is None:
        default_domain = next(iter(state.domain_counts), "code_domain")
        state.active_quest = {
            "quest_id": "bootstrap:code_domain",
            "title": "Work quest",
            "description": "Exploit the best current strategy in the canonical domain.",
            "source": "bootstrap",
            "state": "selected",
            "priority": 0.5,
            "source_payload": {"quest_type": "work_quest", "domain": default_domain},
            "metadata": {"quest_type": "work_quest", "domain": default_domain},
        }
    if not state.quest_portfolio:
        state.quest_portfolio = [dict(state.active_quest)]
    return state


def rebuild_runtime_state(log_dir: str | Path = "data") -> ReplayState:
    return replay_state(log_dir)


def archive_pressure(state: ReplayState, *, window: int = 6) -> Dict[str, float]:
    recent = state.metric_history[-window:]
    if recent:
        novelty_avg = sum(row.get("novelty", 0.0) for row in recent) / len(recent)
        diversity_avg = sum(row.get("diversity", 0.0) for row in recent) / len(recent)
        usefulness_avg = sum(row.get("usefulness", row.get("quality", 0.0)) for row in recent) / len(recent)
        persistence_avg = sum(row.get("persistence", row.get("efficiency", 0.0)) for row in recent) / len(recent)
    else:
        novelty_avg = diversity_avg = usefulness_avg = persistence_avg = 1.0
    recent_failures = len([row for row in state.repairs[-window:] if row.get("event_type") == "repair_failed"])
    archive_size = sum(len(rows) for rows in state.archive.values())
    transfer_pressure = 0.0 if len(state.domain_counts) <= 1 else max(0.0, 0.6 - min(state.domain_counts.values()) / max(1, sum(state.domain_counts.values())))
    concentration = state.lineage_concentration()
    return {
        "exploration": round(max(0.0, 1.0 - novelty_avg), 6),
        "repair": round(min(1.0, recent_failures / max(1, window)), 6),
        "diversity": round(max(0.0, concentration - 0.45) + max(0.0, 0.45 - diversity_avg), 6),
        "replay": round(min(1.0, len(state.tick_summaries[-window:]) / max(1, window)), 6),
        "collapse": round(max(0.0, concentration - 0.68), 6),
        "lineage_concentration": round(concentration, 6),
        "archive_pressure": round(min(1.0, archive_size / 512.0), 6),
        "transfer_pressure": round(transfer_pressure, 6),
        "usefulness_pressure": round(max(0.0, 1.0 - usefulness_avg), 6),
        "persistence_pressure": round(max(0.0, 1.0 - persistence_avg), 6),
    }


__all__ = ["ReplayState", "archive_pressure", "rebuild_runtime_state", "replay_state"]
