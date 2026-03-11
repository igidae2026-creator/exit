from __future__ import annotations

from typing import Any, Dict, Iterable, Sequence, Tuple


def detect_duplicate_events(events: Sequence[Dict[str, Any]]) -> list[Dict[str, Any]]:
    seen: set[Tuple[Any, Any, Any]] = set()
    duplicates = []
    for event in events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        key = (event.get("type"), event.get("ts"), tuple(sorted(payload.items())))
        if key in seen:
            duplicates.append(event)
            continue
        seen.add(key)
    return duplicates


def partial_write_detected(snapshot: Dict[str, Any], required_fields: Iterable[str]) -> bool:
    return any(field not in snapshot for field in required_fields)


def stale_snapshot(snapshot: Dict[str, Any], queue_state: Dict[str, Any]) -> bool:
    snapshot_index = int(snapshot.get("current_index", 0) or 0)
    queue_index = int(queue_state.get("current_index", 0) or 0)
    return snapshot_index < queue_index


def replay_resume_decision(
    events: Sequence[Dict[str, Any]],
    snapshot: Dict[str, Any],
    queue_state: Dict[str, Any],
    required_snapshot_fields: Iterable[str],
) -> Dict[str, Any]:
    if partial_write_detected(snapshot, required_snapshot_fields):
        return {"verdict": "recover", "reason": "partial_write_detected"}
    if stale_snapshot(snapshot, queue_state):
        return {"verdict": "recover", "reason": "stale_snapshot_detected"}
    if detect_duplicate_events(events):
        return {"verdict": "recover", "reason": "duplicate_event_detected"}
    return {"verdict": "resume", "reason": "replay_consistent"}
