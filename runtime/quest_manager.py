"""Quest lifecycle management.

A quest is an exploration objective generated from runtime signals or metrics.
Lifecycle:
- proposed
- selected
- retired
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Literal, Mapping, Optional
import threading
import uuid

QuestState = Literal["proposed", "selected", "retired"]


METRIC_QUEST_HINTS: Dict[str, str] = {
    "quality": "Improve output quality through tighter validation and review loops.",
    "novelty": "Increase novelty by exploring less-used strategy branches.",
    "diversity": "Broaden exploration diversity across strategy families.",
    "efficiency": "Reduce runtime overhead and improve throughput.",
    "cost": "Lower resource usage while preserving target quality.",
}


@dataclass
class Quest:
    """Exploration objective tracked by the quest manager."""

    title: str
    description: str
    source: Literal["signal", "metrics", "manual"]
    state: QuestState = "proposed"
    priority: float = 0.5
    quest_id: str = field(default_factory=lambda: f"q_{uuid.uuid4().hex[:12]}")
    source_payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: _now_iso())
    updated_at: str = field(default_factory=lambda: _now_iso())
    selected_at: Optional[str] = None
    retired_at: Optional[str] = None
    retired_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quest_id": self.quest_id,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "state": self.state,
            "priority": self.priority,
            "source_payload": dict(self.source_payload),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "selected_at": self.selected_at,
            "retired_at": self.retired_at,
            "retired_reason": self.retired_reason,
        }


class QuestManager:
    """In-memory quest manager with strict lifecycle transitions."""

    def __init__(self, *, max_selected: int = 1) -> None:
        if max_selected < 1:
            raise ValueError("max_selected must be >= 1")
        self.max_selected = max_selected
        self._quests: Dict[str, Quest] = {}
        self._lock = threading.RLock()

    def propose(
        self,
        *,
        title: str,
        description: str,
        source: Literal["signal", "metrics", "manual"],
        priority: float = 0.5,
        source_payload: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Quest:
        quest = Quest(
            title=title,
            description=description,
            source=source,
            state="proposed",
            priority=_clamp(priority, 0.0, 1.0),
            source_payload=dict(source_payload or {}),
            metadata=dict(metadata or {}),
        )
        with self._lock:
            self._quests[quest.quest_id] = quest
        return quest

    def generate_from_signal(
        self,
        signal: Mapping[str, Any],
        *,
        priority: float = 0.6,
    ) -> Quest:
        signal_name = str(signal.get("name") or signal.get("type") or "runtime_signal")
        title = f"Investigate signal: {signal_name}"
        description = (
            f"Explore root causes and strategy responses for signal '{signal_name}'."
        )
        return self.propose(
            title=title,
            description=description,
            source="signal",
            priority=priority,
            source_payload=signal,
        )

    def generate_from_metrics(
        self,
        metrics: Mapping[str, float],
        *,
        threshold: float = 0.45,
    ) -> List[Quest]:
        created: List[Quest] = []
        for metric, value in metrics.items():
            if not isinstance(value, (int, float)):
                continue
            if value > threshold:
                continue

            metric_name = str(metric)
            hint = METRIC_QUEST_HINTS.get(
                metric_name,
                "Improve this metric through targeted exploration and iteration.",
            )
            severity = 1.0 - _clamp(float(value), 0.0, 1.0)
            quest = self.propose(
                title=f"Improve metric: {metric_name}",
                description=f"{hint} Current value={value:.3f}, threshold={threshold:.3f}.",
                source="metrics",
                priority=_clamp(severity, 0.0, 1.0),
                source_payload={"metric": metric_name, "value": value, "threshold": threshold},
            )
            created.append(quest)
        return created

    def select(self, quest_id: str) -> Quest:
        with self._lock:
            quest = self._require_quest(quest_id)
            if quest.state != "proposed":
                raise ValueError(f"quest {quest_id} is not in proposed state")

            if len(self.list("selected")) >= self.max_selected:
                raise ValueError("selected quest limit reached; retire one before selecting another")

            now = _now_iso()
            quest.state = "selected"
            quest.selected_at = now
            quest.updated_at = now
            return quest

    def select_next(self) -> Optional[Quest]:
        with self._lock:
            proposed = self.list("proposed")
            if not proposed:
                return None
            proposed.sort(key=lambda q: (-q.priority, q.created_at))
            return self.select(proposed[0].quest_id)

    def retire(self, quest_id: str, *, reason: str = "completed") -> Quest:
        with self._lock:
            quest = self._require_quest(quest_id)
            if quest.state == "retired":
                return quest

            if quest.state not in ("proposed", "selected"):
                raise ValueError(f"invalid state transition: {quest.state} -> retired")

            now = _now_iso()
            quest.state = "retired"
            quest.retired_reason = reason
            quest.retired_at = now
            quest.updated_at = now
            return quest

    def get(self, quest_id: str) -> Optional[Quest]:
        with self._lock:
            return self._quests.get(quest_id)

    def list(self, state: Optional[QuestState] = None) -> List[Quest]:
        with self._lock:
            quests = list(self._quests.values())
            if state is None:
                return quests
            return [q for q in quests if q.state == state]

    def counts(self) -> Dict[QuestState, int]:
        with self._lock:
            return {
                "proposed": len([q for q in self._quests.values() if q.state == "proposed"]),
                "selected": len([q for q in self._quests.values() if q.state == "selected"]),
                "retired": len([q for q in self._quests.values() if q.state == "retired"]),
            }

    def import_quests(self, rows: Iterable[Mapping[str, Any]]) -> int:
        """Load existing quests from dictionaries (best-effort)."""
        loaded = 0
        with self._lock:
            for row in rows:
                try:
                    quest = Quest(
                        quest_id=str(row["quest_id"]),
                        title=str(row["title"]),
                        description=str(row.get("description", "")),
                        source=str(row.get("source", "manual")),  # type: ignore[arg-type]
                        state=str(row.get("state", "proposed")),  # type: ignore[arg-type]
                        priority=float(row.get("priority", 0.5)),
                        source_payload=dict(row.get("source_payload", {})),
                        metadata=dict(row.get("metadata", {})),
                        created_at=str(row.get("created_at", _now_iso())),
                        updated_at=str(row.get("updated_at", _now_iso())),
                        selected_at=row.get("selected_at"),
                        retired_at=row.get("retired_at"),
                        retired_reason=row.get("retired_reason"),
                    )
                except Exception:
                    continue

                if quest.state not in ("proposed", "selected", "retired"):
                    continue
                self._quests[quest.quest_id] = quest
                loaded += 1
        return loaded

    def export_quests(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [q.to_dict() for q in self._quests.values()]

    def _require_quest(self, quest_id: str) -> Quest:
        quest = self._quests.get(quest_id)
        if not quest:
            raise KeyError(f"quest not found: {quest_id}")
        return quest


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
