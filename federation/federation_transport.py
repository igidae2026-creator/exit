from __future__ import annotations

from typing import Any, Mapping, Sequence

def enqueue_transport(queue: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    from federation.federation_state import append_federation_row

    row = {"queue": str(queue), "payload": dict(payload)}
    append_federation_row("transport", row)
    return row


def transport_state(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    send_depth = sum(1 for row in rows if str(row.get("kind", "")) == "transport" and str((row.get("payload") or {}).get("queue", "")) == "send")
    receive_depth = sum(1 for row in rows if str(row.get("kind", "")) == "transport" and str((row.get("payload") or {}).get("queue", "")) == "receive")
    adoption_depth = sum(1 for row in rows if str(row.get("kind", "")) == "transport" and str((row.get("payload") or {}).get("queue", "")) == "adoption")
    deliveries = sum(1 for row in rows if str(row.get("kind", "")) in {"artifact_exchange", "domain_propagation", "policy_diffusion", "knowledge_exchange"})
    adoptions = sum(1 for row in rows if str(row.get("kind", "")).endswith("_adoption"))
    total = max(1.0, float(len(rows) or 1))
    return {
        "send_queue_depth": send_depth,
        "receive_queue_depth": receive_depth,
        "adoption_queue_depth": adoption_depth,
        "transport_delivery_rate": round(deliveries / total, 4),
        "adoption_completion_rate": round(adoptions / total, 4),
    }


__all__ = ["enqueue_transport", "transport_state"]
