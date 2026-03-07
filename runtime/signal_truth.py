from __future__ import annotations

from typing import Any, Mapping

from genesis.event_log import append_event, append_jsonl, ensure_spine, read_jsonl, utc_now

VALID_SOURCES = {"human", "ai", "external", "auto"}
VALID_STATUSES = {"new", "queued", "consumed", "ignored", "failed"}


def append_signal(payload: Mapping[str, Any], *, data_dir: str = "data") -> dict[str, Any]:
    row = {
        "id": str(payload.get("id") or f"signal:{utc_now()}"),
        "ts": str(payload.get("ts") or utc_now()),
        "source": str(payload.get("source") or "auto"),
        "domain_hint": str(payload.get("domain_hint") or "default"),
        "payload": dict(payload.get("payload", {})) if isinstance(payload.get("payload"), Mapping) else {},
        "status": str(payload.get("status") or "new"),
        "consumed_by": payload.get("consumed_by"),
        "priority": float(payload.get("priority", 0.5)),
        "provenance": dict(payload.get("provenance", {})) if isinstance(payload.get("provenance"), Mapping) else {},
        "tags": [str(tag) for tag in payload.get("tags", [])],
        "source_ref": payload.get("source_ref"),
    }
    if row["source"] not in VALID_SOURCES:
        row["source"] = "auto"
    if row["status"] not in VALID_STATUSES:
        row["status"] = "new"
    append_jsonl(ensure_spine(data_dir).signals_path, row)
    append_event("signal_ingested", {"id": row["id"], "status": row["status"]}, data_dir=data_dir)
    return row


def transition_signal(signal_id: str, status: str, *, consumed_by: str | None = None, data_dir: str = "data") -> dict[str, Any]:
    row = append_signal({"id": signal_id, "status": status, "source": "auto", "consumed_by": consumed_by}, data_dir=data_dir)
    append_event(f"signal_{row['status']}", {"id": signal_id, "consumed_by": consumed_by}, data_dir=data_dir)
    return row


def signal_state(*, data_dir: str = "data") -> dict[str, Any]:
    rows = [dict(row) for row in read_jsonl(ensure_spine(data_dir).signals_path)]
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        sid = str(row.get("id") or "")
        if sid:
            latest[sid] = row
    status_counts: dict[str, int] = {}
    for row in latest.values():
        status = str(row.get("status") or "new")
        status_counts[status] = status_counts.get(status, 0) + 1
    return {"total_rows": len(rows), "signals": len(latest), "status_counts": status_counts}
