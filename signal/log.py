from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from uuid import uuid4

from genesis.event_log import append_event, append_jsonl, ensure_spine, read_jsonl, utc_now

VALID_SOURCES = {"human", "ai", "external", "auto"}
VALID_STATUSES = {"new", "queued", "consumed", "ignored", "failed"}


@dataclass(frozen=True, slots=True)
class SignalRecord:
    id: str
    ts: str
    source: str
    domain_hint: str
    payload: dict[str, Any]
    status: str
    consumed_by: str | None
    priority: float
    provenance: dict[str, Any]
    tags: list[str]
    source_ref: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "ts": self.ts,
            "source": self.source,
            "domain_hint": self.domain_hint,
            "payload": dict(self.payload),
            "status": self.status,
            "consumed_by": self.consumed_by,
            "priority": float(self.priority),
            "provenance": dict(self.provenance),
            "tags": list(self.tags),
            "source_ref": self.source_ref,
        }


def _signals_path(data_dir: str = "data"):
    return ensure_spine(data_dir).signals_path


def append_signal(payload: Mapping[str, Any], *, data_dir: str = "data") -> dict[str, Any]:
    source = str(payload.get("source", "auto"))
    status = str(payload.get("status", "new"))
    row = SignalRecord(
        id=str(payload.get("id") or uuid4()),
        ts=str(payload.get("ts") or utc_now()),
        source=source if source in VALID_SOURCES else "auto",
        domain_hint=str(payload.get("domain_hint") or "default"),
        payload=dict(payload.get("payload", {})) if isinstance(payload.get("payload"), Mapping) else {},
        status=status if status in VALID_STATUSES else "new",
        consumed_by=str(payload.get("consumed_by")) if payload.get("consumed_by") else None,
        priority=float(payload.get("priority", 0.5)),
        provenance=dict(payload.get("provenance", {})) if isinstance(payload.get("provenance"), Mapping) else {},
        tags=[str(item) for item in (payload.get("tags") or [])],
        source_ref=str(payload.get("source_ref")) if payload.get("source_ref") else None,
    ).to_dict()
    append_jsonl(_signals_path(data_dir), row)
    append_event("signal_ingested", {"id": row["id"], "status": row["status"], "source": row["source"]}, data_dir=data_dir)
    return row


def transition_signal(signal_id: str, status: str, *, consumed_by: str | None = None, data_dir: str = "data") -> dict[str, Any]:
    target_status = status if status in VALID_STATUSES else "failed"
    row = {
        "id": str(signal_id),
        "ts": utc_now(),
        "source": "auto",
        "domain_hint": "default",
        "payload": {},
        "status": target_status,
        "consumed_by": consumed_by,
        "priority": 0.5,
        "provenance": {"lifecycle": True},
        "tags": ["lifecycle"],
        "source_ref": None,
    }
    append_jsonl(_signals_path(data_dir), row)
    append_event(f"signal_{target_status}", {"id": row["id"], "consumed_by": consumed_by}, data_dir=data_dir)
    return row


def signal_rows(data_dir: str = "data") -> list[dict[str, Any]]:
    return [dict(row) for row in read_jsonl(_signals_path(data_dir))]


def signal_state(data_dir: str = "data") -> dict[str, Any]:
    rows = signal_rows(data_dir)
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        sid = str(row.get("id") or "")
        if sid:
            latest[sid] = dict(row)
    status_counts: dict[str, int] = {k: 0 for k in VALID_STATUSES}
    for row in latest.values():
        status = str(row.get("status") or "new")
        status_counts[status if status in VALID_STATUSES else "failed"] += 1
    return {
        "total_rows": len(rows),
        "signals": len(latest),
        "status_counts": status_counts,
        "queued": [row for row in latest.values() if row.get("status") in {"new", "queued"}],
        "latest": list(latest.values())[-64:],
    }
