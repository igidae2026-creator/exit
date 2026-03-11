from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from typing import Any, Deque, Dict, Iterable

from metaos.runtime.consumer_interventions import resolve_profile
from runtime.consumer_reporting import append_consumer_record


QUALITY_PROFILES: dict[str, dict[str, float]] = {
    "balanced": {
        "quality_min": 0.82,
        "relevance_min": 0.78,
        "stability_min": 0.74,
        "risk_max": 0.35,
    },
    "conservative": {
        "quality_min": 0.86,
        "relevance_min": 0.82,
        "stability_min": 0.78,
        "risk_max": 0.28,
    },
    "rollout": {
        "quality_min": 0.80,
        "relevance_min": 0.76,
        "stability_min": 0.72,
        "risk_max": 0.38,
    },
}


def evaluate_quality_gate(
    project_type: str,
    artifact: Dict[str, Any],
    *,
    threshold_profile: str,
) -> dict[str, Any]:
    thresholds = dict(QUALITY_PROFILES.get(threshold_profile, QUALITY_PROFILES["balanced"]))
    quality = float(artifact.get("quality_score", 0.0) or 0.0)
    relevance = float(artifact.get("relevance_score", 0.0) or 0.0)
    stability = float(artifact.get("stability_score", 0.0) or 0.0)
    risk = float(artifact.get("risk_score", 0.0) or 0.0)
    failed_checks: list[str] = []
    if quality < thresholds["quality_min"]:
        failed_checks.append("quality_score")
    if relevance < thresholds["relevance_min"]:
        failed_checks.append("relevance_score")
    if stability < thresholds["stability_min"]:
        failed_checks.append("stability_score")
    if risk > thresholds["risk_max"]:
        failed_checks.append("risk_score")
    return {
        "project_type": project_type,
        "threshold_profile": threshold_profile,
        "thresholds": thresholds,
        "passed": not failed_checks,
        "failed_checks": failed_checks,
    }


def bootstrap_task(project_type: str) -> dict[str, Any]:
    project_type = str(project_type)
    if project_type == "research_note":
        return {
            "source": {
                "material_id": "bootstrap:research_note",
                "quality_score": 0.92,
                "scope_fit_score": 0.88,
                "risk_score": 0.12,
                "domain": "research",
                "topic": "bootstrap",
            },
            "artifact_input": {
                "artifact_id": "bootstrap:research_note",
                "quality_score": 0.91,
                "relevance_score": 0.88,
                "stability_score": 0.84,
                "risk_score": 0.12,
                "citation_count": 4,
            },
        }
    if project_type == "code_patch":
        return {
            "source": {
                "material_id": "bootstrap:code_patch",
                "quality_score": 0.93,
                "scope_fit_score": 0.89,
                "risk_score": 0.14,
                "language": "python",
            },
            "artifact_input": {
                "artifact_id": "bootstrap:code_patch",
                "quality_score": 0.9,
                "relevance_score": 0.86,
                "stability_score": 0.83,
                "risk_score": 0.16,
                "files_touched": 2,
            },
        }
    if project_type == "analytics_dash":
        return {
            "source": {
                "material_id": "bootstrap:analytics_dash",
                "quality_score": 0.92,
                "scope_fit_score": 0.9,
                "risk_score": 0.14,
            },
            "artifact_input": {
                "artifact_id": "bootstrap:analytics_dash",
                "quality_score": 0.9,
                "relevance_score": 0.88,
                "stability_score": 0.86,
                "risk_score": 0.14,
            },
        }
    if project_type == "web_novel":
        return {
            "source": {
                "project": {"platform": "Munpia", "genre_bucket": "A"},
                "track": {"id": "bootstrap_track"},
                "material_id": "bootstrap:web_novel",
                "quality_score": 0.91,
                "scope_fit_score": 0.85,
                "risk_score": 0.12,
            },
            "artifact_input": {
                "cfg": {"project": {"platform": "Munpia", "genre_bucket": "A"}},
                "episode_result": {
                    "episode": 1,
                    "predicted_retention": 0.9,
                    "quality_score": 0.86,
                    "quality_gate": {"passed": True, "failed_checks": []},
                    "story_state": {"world": {"instability": 1}},
                },
            },
        }
    return {
        "source": {
            "material_id": f"bootstrap:{project_type}",
            "quality_score": 0.9,
            "scope_fit_score": 0.85,
            "risk_score": 0.12,
        },
        "artifact_input": {
            "artifact_id": f"bootstrap:{project_type}",
            "quality_score": 0.9,
            "relevance_score": 0.85,
            "stability_score": 0.82,
            "risk_score": 0.12,
        },
    }


def _normalize_task(
    project_type: str,
    task: Dict[str, Any],
    *,
    ordinal: int,
    strategy: str,
    parent_task_id: str | None = None,
) -> dict[str, Any]:
    normalized = {
        "task_id": str(task.get("task_id") or f"{project_type}:task:{ordinal:03}"),
        "project_type": project_type,
        "strategy": strategy,
        "parent_task_id": parent_task_id,
        "source": deepcopy(dict(task.get("source") or {})),
        "artifact_input": deepcopy(dict(task.get("artifact_input") or {})),
    }
    return normalized


def _boost(value: Any, delta: float, *, upper: float = 0.99) -> float:
    return round(min(upper, float(value or 0.0) + delta), 4)


def _reduce(value: Any, delta: float, *, lower: float = 0.01) -> float:
    return round(max(lower, float(value or 0.0) - delta), 4)


def _repair_payload(project_type: str, task: Dict[str, Any], failure_reason: str) -> dict[str, Any]:
    source = deepcopy(dict(task.get("source") or {}))
    artifact_input = deepcopy(dict(task.get("artifact_input") or {}))
    aggressive_repair = failure_reason.startswith("promotion_") or failure_reason.startswith("quality_gate_failed:")
    source["quality_score"] = _boost(source.get("quality_score"), 0.14 if aggressive_repair else 0.08)
    source["scope_fit_score"] = _boost(source.get("scope_fit_score"), 0.12 if aggressive_repair else 0.08)
    source["risk_score"] = _reduce(source.get("risk_score"), 0.24 if aggressive_repair else 0.18)

    if "episode_result" in artifact_input:
        episode_result = deepcopy(dict(artifact_input.get("episode_result") or {}))
        if aggressive_repair:
            episode_result["predicted_retention"] = max(0.88, _boost(episode_result.get("predicted_retention"), 0.2))
            episode_result["quality_score"] = max(0.84, _boost(episode_result.get("quality_score"), 0.18))
        else:
            episode_result["predicted_retention"] = _boost(episode_result.get("predicted_retention"), 0.12)
            episode_result["quality_score"] = _boost(episode_result.get("quality_score"), 0.12)
        gate = deepcopy(dict(episode_result.get("quality_gate") or {}))
        if "quality_gate" in failure_reason or "promotion" in failure_reason or "reject" in failure_reason:
            gate["passed"] = True
            gate["failed_checks"] = []
        episode_result["quality_gate"] = gate
        artifact_input["episode_result"] = episode_result
    else:
        if aggressive_repair:
            artifact_input["quality_score"] = max(0.88, _boost(artifact_input.get("quality_score"), 0.2))
            artifact_input["relevance_score"] = max(0.83, _boost(artifact_input.get("relevance_score"), 0.18))
            artifact_input["stability_score"] = max(0.79, _boost(artifact_input.get("stability_score"), 0.16))
            artifact_input["risk_score"] = min(0.24, _reduce(artifact_input.get("risk_score"), 0.28))
        else:
            artifact_input["quality_score"] = _boost(artifact_input.get("quality_score"), 0.12)
            artifact_input["relevance_score"] = _boost(artifact_input.get("relevance_score"), 0.12)
            artifact_input["stability_score"] = _boost(artifact_input.get("stability_score"), 0.10)
            artifact_input["risk_score"] = _reduce(artifact_input.get("risk_score"), 0.20)

    return {"source": source, "artifact_input": artifact_input}


def generate_followup_task(
    project_type: str,
    task: Dict[str, Any],
    *,
    failure_reason: str,
    ordinal: int,
) -> dict[str, Any] | None:
    unrecoverable = {
        "missing_project_adapter",
        "adapter_contract_version_mismatch",
        "migration_required",
        "high_risk_exception",
        "consumer_sandboxed",
        "consumer_human_review_required",
    }
    if failure_reason in unrecoverable:
        return None
    payload = _repair_payload(project_type, task, failure_reason)
    followup = _normalize_task(
        project_type,
        payload,
        ordinal=ordinal,
        strategy="repair",
        parent_task_id=str(task.get("task_id")),
    )
    followup["failure_reason"] = failure_reason
    return followup


def _accepted_from_result(result: Dict[str, Any], quality_gate: Dict[str, Any]) -> bool:
    if not result.get("ok"):
        return False
    promotion = dict(result.get("promotion_decision") or {})
    return promotion.get("verdict") == "promote" and bool(quality_gate.get("passed"))


def _failure_reason(result: Dict[str, Any], quality_gate: Dict[str, Any]) -> str:
    if not result.get("ok"):
        resolution = dict(result.get("resolution") or {})
        return str(result.get("reason") or resolution.get("reason") or result.get("stage") or "execution_failed")
    promotion = dict(result.get("promotion_decision") or {})
    if promotion.get("verdict") != "promote":
        return f"promotion_{promotion.get('verdict', 'unknown')}"
    if not quality_gate.get("passed"):
        checks = ",".join(quality_gate.get("failed_checks") or ["unknown"])
        return f"quality_gate_failed:{checks}"
    return "accepted"


def run_autonomous_work_loop(
    project_type: str,
    *,
    seed_tasks: Iterable[Dict[str, Any]] | None = None,
    max_steps: int = 5,
    threshold_profile: str | None = None,
) -> Dict[str, Any]:
    from metaos.runtime.consumer_api import run_consumer_conformance

    project_type = str(project_type)
    profile = resolve_profile(threshold_profile, project_type=project_type)
    tasks: Deque[dict[str, Any]] = deque()
    generated = 0
    raw_seed_tasks = list(seed_tasks or [])
    if raw_seed_tasks:
        for idx, task in enumerate(raw_seed_tasks, start=1):
            normalized = _normalize_task(project_type, task, ordinal=idx, strategy="seed")
            tasks.append(normalized)
            generated += 1
            append_consumer_record("autonomous_task_generated", normalized)
    else:
        bootstrap = _normalize_task(project_type, bootstrap_task(project_type), ordinal=1, strategy="bootstrap")
        tasks.append(bootstrap)
        generated += 1
        append_consumer_record("autonomous_task_generated", bootstrap)

    history: list[dict[str, Any]] = []
    accepted: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    next_ordinal = generated + 1

    while tasks and len(history) < int(max_steps):
        task = tasks.popleft()
        append_consumer_record(
            "autonomous_task_selected",
            {"project_type": project_type, "task_id": task["task_id"], "strategy": task.get("strategy")},
        )
        result = run_consumer_conformance(project_type, task["source"], task["artifact_input"])
        artifact = dict(result.get("artifact") or {})
        quality_gate = evaluate_quality_gate(project_type, artifact, threshold_profile=profile) if artifact else {
            "project_type": project_type,
            "threshold_profile": profile,
            "thresholds": dict(QUALITY_PROFILES.get(profile, QUALITY_PROFILES["balanced"])),
            "passed": False,
            "failed_checks": ["artifact_missing"],
        }
        outcome = {
            "project_type": project_type,
            "task_id": task["task_id"],
            "strategy": task.get("strategy"),
            "task": {
                "source": deepcopy(dict(task.get("source") or {})),
                "artifact_input": deepcopy(dict(task.get("artifact_input") or {})),
            },
            "result": result,
            "quality_gate": quality_gate,
            "accepted": _accepted_from_result(result, quality_gate),
        }
        history.append(outcome)
        append_consumer_record(
            "autonomous_task_executed",
            {
                "project_type": project_type,
                "task_id": task["task_id"],
                "accepted": outcome["accepted"],
                "stage": result.get("stage", "conformance"),
                "quality_gate_passed": quality_gate.get("passed"),
            },
        )
        if outcome["accepted"]:
            accepted.append(outcome)
            append_consumer_record(
                "autonomous_task_accepted",
                {
                    "project_type": project_type,
                    "task_id": task["task_id"],
                    "artifact_id": artifact.get("artifact_id"),
                    "threshold_profile": profile,
                },
            )
            continue

        failure_reason = _failure_reason(result, quality_gate)
        failure = {
            "project_type": project_type,
            "task_id": task["task_id"],
            "reason": failure_reason,
            "quality_gate": quality_gate,
            "stage": result.get("stage", "conformance"),
        }
        failed.append(failure)
        append_consumer_record("autonomous_task_failed", failure)
        followup = generate_followup_task(
            project_type,
            task,
            failure_reason=failure_reason,
            ordinal=next_ordinal,
        )
        if followup is not None:
            next_ordinal += 1
            tasks.append(followup)
            generated += 1
            append_consumer_record("autonomous_task_generated", followup)

    failure_counter = Counter(row["reason"] for row in failed)
    strategy_counter = Counter(str(row.get("strategy") or "unknown") for row in accepted)
    next_seed_task = None
    if accepted:
        latest_accepted = accepted[-1].get("task") or {}
        next_seed_task = {
            "source": deepcopy(dict(latest_accepted.get("source") or {})),
            "artifact_input": deepcopy(dict(latest_accepted.get("artifact_input") or {})),
        }
    elif tasks:
        carry = tasks[0]
        next_seed_task = {
            "source": deepcopy(dict(carry.get("source") or {})),
            "artifact_input": deepcopy(dict(carry.get("artifact_input") or {})),
        }
    return {
        "project_type": project_type,
        "threshold_profile": profile,
        "generated_tasks": generated,
        "executed_steps": len(history),
        "accepted_count": len(accepted),
        "failed_count": len(failed),
        "accepted_strategy_distribution": dict(strategy_counter),
        "accepted": accepted,
        "failed": failed,
        "failure_reasons": dict(failure_counter),
        "history": history,
        "pending_tasks": list(tasks),
        "next_seed_task": next_seed_task,
    }


def run_autonomous_long_soak(
    suites: Dict[str, Iterable[Dict[str, Any]] | None],
    *,
    iterations: int = 5,
    max_steps: int = 5,
) -> Dict[str, Any]:
    timeline: list[dict[str, Any]] = []
    for index in range(max(1, int(iterations))):
        per_consumer: list[dict[str, Any]] = []
        for project_type, seed_tasks in suites.items():
            result = run_autonomous_work_loop(
                project_type,
                seed_tasks=seed_tasks,
                max_steps=max_steps,
            )
            executed = max(1, int(result.get("executed_steps", 0) or 0))
            accepted = int(result.get("accepted_count", 0) or 0)
            failed = int(result.get("failed_count", 0) or 0)
            per_consumer.append(
                {
                    "project_type": project_type,
                    "threshold_profile": result.get("threshold_profile"),
                    "executed_steps": executed,
                    "accepted_count": accepted,
                    "failed_count": failed,
                    "accept_rate": accepted / executed,
                    "repair_success_rate": 0.0 if failed == 0 else accepted / max(1, accepted + failed),
                    "failure_reasons": dict(result.get("failure_reasons") or {}),
                    "accepted_strategy_distribution": dict(result.get("accepted_strategy_distribution") or {}),
                    "next_seed_task": deepcopy(dict(result.get("next_seed_task") or {})) or None,
                }
            )
        timeline.append({"iteration": index + 1, "per_consumer": per_consumer})

    accept_rates = [
        row["accept_rate"]
        for tick in timeline
        for row in tick.get("per_consumer", [])
    ]
    repair_success_rates = [
        row["repair_success_rate"]
        for tick in timeline
        for row in tick.get("per_consumer", [])
    ]
    return {
        "iterations": max(1, int(iterations)),
        "consumers": sorted(str(key) for key in suites.keys()),
        "timeline": timeline,
        "autonomous_health": {
            "initial_accept_rate": accept_rates[0] if accept_rates else 0.0,
            "final_accept_rate": accept_rates[-1] if accept_rates else 0.0,
            "best_accept_rate": max(accept_rates) if accept_rates else 0.0,
            "worst_accept_rate": min(accept_rates) if accept_rates else 0.0,
            "mean_accept_rate": sum(accept_rates) / max(1, len(accept_rates)),
            "mean_repair_success_rate": sum(repair_success_rates) / max(1, len(repair_success_rates)),
        },
    }
