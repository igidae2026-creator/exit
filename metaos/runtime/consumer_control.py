from __future__ import annotations

from typing import Any, Dict

from metaos.runtime.consumer_reporting import read_consumer_records


def consumer_control_state() -> Dict[str, Any]:
    state: Dict[str, Any] = {
        "global": {
            "rollout_state": "open",
            "migration_state": "idle",
        },
        "consumers": {},
    }
    for row in read_consumer_records():
        if row.get("record_type") != "consumer_intervention":
            continue
        payload = dict(row.get("payload") or {})
        action = str(payload.get("action") or "")
        project_type = payload.get("project_type")
        if action == "pause_new_rollouts":
            state["global"]["rollout_state"] = "paused"
        elif action == "drain_migration_queue":
            state["global"]["migration_state"] = "draining"
        elif project_type:
            consumer = state["consumers"].setdefault(
                str(project_type),
                {
                    "operating_state": "active",
                    "last_action": None,
                    "reason": None,
                },
            )
            if action == "inspect_consumer":
                consumer["operating_state"] = "inspection_pending"
            elif action == "sandbox_consumer":
                consumer["operating_state"] = "sandboxed"
            elif action == "require_human_review":
                consumer["operating_state"] = "human_review_required"
            consumer["last_action"] = action
            consumer["reason"] = payload.get("reason")
    return state


def consumer_control_decision(project_type: str | None = None) -> Dict[str, Any]:
    state = consumer_control_state()
    if state["global"]["rollout_state"] == "paused":
        return {
            "allowed": True,
            "verdict": "accept",
            "reason": "global_rollout_paused_monitor_only",
            "state": state,
        }

    if not project_type:
        return {"allowed": True, "verdict": "accept", "reason": "control_open", "state": state}

    consumer = state["consumers"].get(str(project_type))
    if not consumer:
        return {"allowed": True, "verdict": "accept", "reason": "control_open", "state": state}

    operating_state = consumer.get("operating_state")
    if operating_state == "sandboxed":
        return {
            "allowed": False,
            "verdict": "reject",
            "reason": "consumer_sandboxed",
            "state": state,
        }
    if operating_state == "inspection_pending":
        return {
            "allowed": True,
            "verdict": "accept",
            "reason": "inspection_pending_monitor_only",
            "state": state,
        }
    if operating_state == "human_review_required":
        return {
            "allowed": False,
            "verdict": "hold",
            "reason": str(operating_state),
            "state": state,
        }
    return {"allowed": True, "verdict": "accept", "reason": "control_open", "state": state}


def projected_queue_state(project_type: str | None = None, *, active_job_id: str | None = None) -> Dict[str, Any]:
    decision = consumer_control_decision(project_type)
    if decision.get("allowed", True):
        return {
            "queue_status": "running",
            "jobs": [] if not active_job_id else [{"job_id": active_job_id, "job_type": "scope_evaluate", "status": "running", "payload": {}}],
        }
    status = "paused" if decision.get("verdict") == "hold" else "blocked"
    return {
        "queue_status": status,
        "jobs": [] if not active_job_id else [{"job_id": active_job_id, "job_type": "scope_evaluate", "status": "cancelled", "payload": {}}],
        "control_reason": decision.get("reason"),
    }


def projected_supervisor_state(project_type: str | None = None, *, active_job_id: str | None = None) -> Dict[str, Any]:
    decision = consumer_control_decision(project_type)
    if decision.get("allowed", True):
        return {"status": "running", "active_job_id": active_job_id}
    status = "paused" if decision.get("verdict") == "hold" else "blocked"
    return {
        "status": status,
        "active_job_id": active_job_id,
        "control_reason": decision.get("reason"),
    }
