from __future__ import annotations

from typing import Any, Dict, List

from runtime.consumer_control import consumer_control_state
from runtime.consumer_reporting import append_consumer_record, consumer_operating_report


THRESHOLD_PROFILES: Dict[str, Dict[str, float]] = {
    "balanced": {
        "global_escalate_rate": 0.2,
        "consumer_hold_rate": 0.4,
        "consumer_reject_rate": 0.4,
        "consumer_escalate_rate": 0.2,
    },
    "conservative": {
        "global_escalate_rate": 0.15,
        "consumer_hold_rate": 0.3,
        "consumer_reject_rate": 0.3,
        "consumer_escalate_rate": 0.15,
    },
    "rollout": {
        "global_escalate_rate": 0.25,
        "consumer_hold_rate": 0.45,
        "consumer_reject_rate": 0.45,
        "consumer_escalate_rate": 0.25,
    },
}

DEFAULT_PROFILE_BY_CONSUMER: Dict[str, str] = {
    "research_note": "conservative",
    "code_patch": "balanced",
    "analytics_dash": "balanced",
    "web_novel": "balanced",
}


def threshold_profile(profile: str = "balanced") -> Dict[str, float]:
    return dict(THRESHOLD_PROFILES.get(str(profile), THRESHOLD_PROFILES["balanced"]))


def default_profile_for_consumer(project_type: str | None = None) -> str:
    if not project_type:
        return "balanced"
    return str(DEFAULT_PROFILE_BY_CONSUMER.get(str(project_type), "balanced"))


def resolve_profile(profile: str | None = None, *, project_type: str | None = None) -> str:
    if profile:
        return str(profile)
    return default_profile_for_consumer(project_type)


def recommended_interventions(
    report: Dict[str, Any] | None = None,
    *,
    profile: str | None = None,
    project_type: str | None = None,
) -> List[Dict[str, Any]]:
    report = report or consumer_operating_report()
    profile = resolve_profile(profile, project_type=project_type)
    thresholds = threshold_profile(profile)
    actions: List[Dict[str, Any]] = []
    if report.get("escalate_rate", 0.0) >= thresholds["global_escalate_rate"]:
        actions.append({"action": "pause_new_rollouts", "reason": "high_escalate_rate", "profile": profile})
    if report.get("migration_queue"):
        actions.append({"action": "drain_migration_queue", "reason": "migration_debt", "profile": profile})
    for row in report.get("consumer_health_rollup", []):
        project_type = row.get("project_type")
        if float(row.get("hold_rate", 0.0) or 0.0) >= thresholds["consumer_hold_rate"]:
            actions.append({"action": "inspect_consumer", "project_type": project_type, "reason": "high_hold_rate", "profile": profile})
        if float(row.get("reject_rate", 0.0) or 0.0) >= thresholds["consumer_reject_rate"]:
            actions.append({"action": "sandbox_consumer", "project_type": project_type, "reason": "high_reject_rate", "profile": profile})
        if float(row.get("escalate_rate", 0.0) or 0.0) >= thresholds["consumer_escalate_rate"]:
            actions.append({"action": "require_human_review", "project_type": project_type, "reason": "high_escalate_rate", "profile": profile})
    return actions


def intervention_status(*, profile: str | None = None, project_type: str | None = None) -> Dict[str, Any]:
    report = consumer_operating_report()
    profile = resolve_profile(profile, project_type=project_type)
    return {
        "report": report,
        "threshold_profile": profile,
        "thresholds": threshold_profile(profile),
        "recommended_actions": recommended_interventions(report, profile=profile),
    }


def apply_interventions(
    report: Dict[str, Any] | None = None,
    *,
    profile: str | None = None,
    project_type: str | None = None,
) -> Dict[str, Any]:
    report = report or consumer_operating_report()
    profile = resolve_profile(profile, project_type=project_type)
    actions = recommended_interventions(report, profile=profile)
    applied: List[Dict[str, Any]] = []
    for action in actions:
        row = {
            "action": str(action.get("action") or "unknown_action"),
            "project_type": action.get("project_type"),
            "reason": str(action.get("reason") or "unspecified"),
            "profile": str(action.get("profile") or profile),
            "status": "applied",
        }
        if row["action"] == "pause_new_rollouts":
            row["target_scope"] = "global"
            row["target_state"] = "rollout_paused"
        elif row["action"] == "drain_migration_queue":
            row["target_scope"] = "global"
            row["target_state"] = "migration_draining"
        elif row["action"] == "inspect_consumer":
            row["target_scope"] = "consumer"
            row["target_state"] = "inspection_pending"
        elif row["action"] == "sandbox_consumer":
            row["target_scope"] = "consumer"
            row["target_state"] = "sandboxed"
        elif row["action"] == "require_human_review":
            row["target_scope"] = "consumer"
            row["target_state"] = "human_review_required"
        append_consumer_record("consumer_intervention", row)
        applied.append(row)
    return {
        "report": report,
        "threshold_profile": profile,
        "thresholds": threshold_profile(profile),
        "recommended_actions": actions,
        "applied_actions": applied,
        "control_state": consumer_control_state(),
    }
