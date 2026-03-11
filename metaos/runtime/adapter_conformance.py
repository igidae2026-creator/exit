from __future__ import annotations

from typing import Any, Dict

from metaos.runtime.adapter_registry import adapter_resolution, get_adapter_manifest
from metaos.runtime.adapter_runtime_contracts import validate_job_queue, validate_policy_decision, validate_supervisor


def _apply_scope_policy(material: Dict[str, Any]) -> Dict[str, Any]:
    quality = float(material.get("quality_score", 0.0) or 0.0)
    scope_fit = float(material.get("scope_fit_score", 0.0) or 0.0)
    risk = float(material.get("risk_score", 0.0) or 0.0)
    material_id = str(material.get("material_id") or "unknown_material")
    if risk >= 0.9:
        return {"verdict": "escalate", "reason": "high_risk_exception", "material_id": material_id}
    if quality >= 0.8 and scope_fit >= 0.75 and risk <= 0.35:
        return {"verdict": "accept", "reason": "normal_scope_fit", "material_id": material_id}
    if risk >= 0.7 or scope_fit <= 0.35:
        return {"verdict": "reject", "reason": "out_of_scope_or_risky", "material_id": material_id}
    return {"verdict": "hold", "reason": "borderline_needs_review_buffer", "material_id": material_id}


def _apply_promotion_policy(artifact: Dict[str, Any]) -> Dict[str, Any]:
    quality = float(artifact.get("quality_score", 0.0) or 0.0)
    relevance = float(artifact.get("relevance_score", 0.0) or 0.0)
    stability = float(artifact.get("stability_score", 0.0) or 0.0)
    risk = float(artifact.get("risk_score", 0.0) or 0.0)
    artifact_id = str(artifact.get("artifact_id") or "unknown_artifact")
    if risk >= 0.9:
        return {"verdict": "escalate", "reason": "high_risk_exception", "artifact_id": artifact_id}
    if quality >= 0.85 and relevance >= 0.8 and stability >= 0.75 and risk <= 0.3:
        return {"verdict": "promote", "reason": "promotion_ready", "artifact_id": artifact_id}
    if quality <= 0.45 or relevance <= 0.4 or risk >= 0.72:
        return {"verdict": "reject", "reason": "not_promotion_worthy", "artifact_id": artifact_id}
    return {"verdict": "hold", "reason": "borderline_candidate", "artifact_id": artifact_id}


def run_adapter_conformance(project_type: str, source: Dict[str, Any], artifact_input: Dict[str, Any]) -> Dict[str, Any]:
    resolution = adapter_resolution(project_type)
    if resolution["verdict"] != "accept":
        return {"ok": False, "stage": "adapter_resolution", "resolution": resolution}
    manifest = get_adapter_manifest(project_type)
    assert manifest is not None

    material = manifest["material_from_source"](source)
    scope_decision = _apply_scope_policy(material)
    ok, reason = validate_policy_decision(scope_decision)
    if not ok:
        return {"ok": False, "stage": "scope_policy", "reason": reason}

    queue_state = {
        "queue_status": "running",
        "jobs": [
            {
                "job_id": f"scope:{material['material_id']}",
                "job_type": "scope_evaluate",
                "status": "running",
                "payload": {"material_id": material["material_id"]},
            }
        ],
    }
    queue_ok, queue_reason = validate_job_queue(queue_state)
    if not queue_ok:
        return {"ok": False, "stage": "job_queue_contract", "reason": queue_reason}

    supervisor_state = {"status": "running", "active_job_id": queue_state["jobs"][0]["job_id"]}
    supervisor_ok, supervisor_reason = validate_supervisor(supervisor_state)
    if not supervisor_ok:
        return {"ok": False, "stage": "supervisor_contract", "reason": supervisor_reason}

    artifact = manifest["artifact_from_output"](artifact_input)
    promote_decision = _apply_promotion_policy(artifact)
    promote_ok, promote_reason = validate_policy_decision(promote_decision)
    if not promote_ok:
        return {"ok": False, "stage": "promotion_policy", "reason": promote_reason}

    return {
        "ok": True,
        "resolution": resolution,
        "scope_decision": scope_decision,
        "promotion_decision": promote_decision,
        "queue_state": queue_state,
        "supervisor_state": supervisor_state,
        "artifact": artifact,
    }
