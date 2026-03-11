from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple


RUNTIME_CONTRACT_VERSION = "1.0.0"

EVENT_TYPES = {
    "ingest_material",
    "scope_evaluate",
    "promote_material",
    "reject_material",
    "defer_material",
    "generate_artifact",
    "rewrite_artifact",
    "artifact_rejected",
    "certify_artifact",
    "pause_queue",
    "resume_queue",
    "recover_failed_job",
    "job_queue_synced",
    "supervisor_snapshot_updated",
    "admission_decision_recorded",
    "promotion_decision_recorded",
}

JOB_TYPES = {
    "ingest_material",
    "scope_evaluate",
    "promote_material",
    "generate_artifact",
    "rewrite_artifact",
    "certify_artifact",
    "recover_failed_job",
}

JOB_STATUSES = {"queued", "running", "completed", "failed", "rejected", "cancelled"}
QUEUE_STATUSES = {"idle", "running", "paused", "blocked", "done"}
SUPERVISOR_STATUSES = {"idle", "running", "paused", "blocked", "recovering", "stopped", "done"}
POLICY_VERDICTS = {"accept", "hold", "reject", "escalate", "sandbox", "promote"}

CONFORMANCE_CHECKS = [
    "adapter_resolution",
    "scope_policy",
    "admission_snapshot",
    "job_queue_contract",
    "supervisor_contract",
    "artifact_normalization",
    "promotion_policy",
    "promotion_snapshot",
]


def _has_fields(obj: Dict[str, Any], fields: Iterable[str]) -> Tuple[bool, str]:
    for field in fields:
        if field not in obj:
            return False, f"missing_{field}"
    return True, "ok"


def validate_policy_decision(decision: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(decision, dict):
        return False, "decision_not_dict"
    ok, reason = _has_fields(decision, ["verdict", "reason"])
    if not ok:
        return ok, reason
    if decision.get("verdict") not in POLICY_VERDICTS:
        return False, "invalid_policy_verdict"
    return True, "ok"


def validate_job_queue(queue_state: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(queue_state, dict):
        return False, "queue_not_dict"
    ok, reason = _has_fields(queue_state, ["queue_status", "jobs"])
    if not ok:
        return ok, reason
    if queue_state.get("queue_status") not in QUEUE_STATUSES:
        return False, "invalid_queue_status"
    if not isinstance(queue_state.get("jobs"), list):
        return False, "jobs_not_list"
    for job in queue_state.get("jobs", []):
        if not isinstance(job, dict):
            return False, "job_not_dict"
        ok, reason = _has_fields(job, ["job_id", "job_type", "status", "payload"])
        if not ok:
            return ok, reason
        if job.get("job_type") not in JOB_TYPES:
            return False, "invalid_job_type"
        if job.get("status") not in JOB_STATUSES:
            return False, "invalid_job_status"
    return True, "ok"


def validate_supervisor(supervisor_state: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(supervisor_state, dict):
        return False, "supervisor_not_dict"
    ok, reason = _has_fields(supervisor_state, ["status"])
    if not ok:
        return ok, reason
    if supervisor_state.get("status") not in SUPERVISOR_STATUSES:
        return False, "invalid_supervisor_status"
    return True, "ok"


def compatibility_report(runtime_version: str, adapter_version: str) -> Dict[str, Any]:
    if runtime_version == adapter_version:
        return {
            "runtime_version": runtime_version,
            "adapter_version": adapter_version,
            "compatible": True,
            "migration_required": False,
        }
    return {
        "runtime_version": runtime_version,
        "adapter_version": adapter_version,
        "compatible": False,
        "migration_required": True,
    }
