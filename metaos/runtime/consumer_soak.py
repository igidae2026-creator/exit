from __future__ import annotations

from typing import Any, Dict, List

from metaos.runtime.consumer_api import run_consumer_stress
from metaos.runtime.consumer_control import consumer_control_state
from metaos.runtime.consumer_interventions import apply_interventions, recommended_interventions, resolve_profile
from metaos.runtime.consumer_reporting import clear_consumer_records, consumer_operating_report


def _observed_verdict(result: Dict[str, Any]) -> str:
    if result.get("ok"):
        promotion = dict(result.get("promotion_decision") or {})
        scope = dict(result.get("scope_decision") or {})
        return str(promotion.get("verdict") or scope.get("verdict") or "accept")
    resolution = dict(result.get("resolution") or {})
    return str(resolution.get("verdict") or result.get("stage") or "unknown")


def _observed_reason(result: Dict[str, Any]) -> str:
    if result.get("ok"):
        promotion = dict(result.get("promotion_decision") or {})
        scope = dict(result.get("scope_decision") or {})
        return str(promotion.get("reason") or scope.get("reason") or "ok")
    resolution = dict(result.get("resolution") or {})
    return str(resolution.get("reason") or result.get("reason") or result.get("stage") or "unknown")


def _calibration_summary(results: List[Dict[str, Any]], scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary = {
        "labeled_cases": 0,
        "matches": 0,
        "false_hold": 0,
        "false_reject": 0,
        "false_escalate": 0,
        "false_promote": 0,
        "false_hold_reasons": {},
    }
    false_hold_reasons: Dict[str, int] = {}
    for result, scenario in zip(results, scenarios):
        expected = scenario.get("expected_verdict")
        if not expected:
            continue
        observed = _observed_verdict(result)
        summary["labeled_cases"] += 1
        if observed == expected:
            summary["matches"] += 1
            continue
        if observed == "hold":
            summary["false_hold"] += 1
            reason = _observed_reason(result)
            false_hold_reasons[reason] = false_hold_reasons.get(reason, 0) + 1
        elif observed == "reject":
            summary["false_reject"] += 1
        elif observed == "escalate":
            summary["false_escalate"] += 1
        elif observed == "promote":
            summary["false_promote"] += 1
    labeled = summary["labeled_cases"] or 1
    summary["match_rate"] = summary["matches"] / labeled
    summary["false_hold_reasons"] = dict(sorted(false_hold_reasons.items(), key=lambda item: (-item[1], item[0])))
    return summary


def _horizon_health(timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
    match_rates: List[float] = []
    false_holds = 0
    false_rejects = 0
    false_escalates = 0
    false_promotes = 0
    late_health_regressions = 0
    late_window = max(1, len(timeline) // 3)
    for tick in timeline:
        per_consumer = list(tick.get("per_consumer", []))
        if not per_consumer:
            continue
        avg_match = sum(float((row.get("calibration") or {}).get("match_rate", 0.0) or 0.0) for row in per_consumer) / len(per_consumer)
        match_rates.append(avg_match)
        false_holds += sum(int((row.get("calibration") or {}).get("false_hold", 0) or 0) for row in per_consumer)
        false_rejects += sum(int((row.get("calibration") or {}).get("false_reject", 0) or 0) for row in per_consumer)
        false_escalates += sum(int((row.get("calibration") or {}).get("false_escalate", 0) or 0) for row in per_consumer)
        false_promotes += sum(int((row.get("calibration") or {}).get("false_promote", 0) or 0) for row in per_consumer)
    if match_rates:
        baseline = max(match_rates[:late_window])
        for rate in match_rates[-late_window:]:
            if rate + 0.05 < baseline:
                late_health_regressions += 1
    return {
        "iterations_observed": len(match_rates),
        "initial_match_rate": match_rates[0] if match_rates else 0.0,
        "final_match_rate": match_rates[-1] if match_rates else 0.0,
        "best_match_rate": max(match_rates) if match_rates else 0.0,
        "worst_match_rate": min(match_rates) if match_rates else 0.0,
        "late_health_regressions": late_health_regressions,
        "false_hold_total": false_holds,
        "false_reject_total": false_rejects,
        "false_escalate_total": false_escalates,
        "false_promote_total": false_promotes,
    }


def run_consumer_soak_suite(
    project_type: str,
    scenarios: List[Dict[str, Any]],
    *,
    iterations: int = 3,
    clear_ledger: bool = True,
    threshold_profile: str | None = None,
) -> Dict[str, Any]:
    threshold_profile = resolve_profile(threshold_profile, project_type=project_type)
    if clear_ledger:
        clear_consumer_records()

    per_iteration: List[Dict[str, Any]] = []
    for index in range(max(1, int(iterations))):
        results = run_consumer_stress(project_type, scenarios)
        report = consumer_operating_report()
        calibration = _calibration_summary(results, scenarios)
        per_iteration.append(
            {
                "iteration": index + 1,
                "scenario_count": len(scenarios),
                "ok_count": sum(1 for row in results if row.get("ok")),
                "verdict_distribution": dict(report.get("verdict_distribution", {})),
                "escalate_rate": float(report.get("escalate_rate", 0.0) or 0.0),
                "recommended_actions": recommended_interventions(report, profile=threshold_profile),
                "calibration": calibration,
            }
        )

    final_report = consumer_operating_report()
    intervention_result = apply_interventions(final_report, profile=threshold_profile)
    return {
        "project_type": project_type,
        "iterations": max(1, int(iterations)),
        "scenario_count": len(scenarios),
        "threshold_profile": threshold_profile,
        "per_iteration": per_iteration,
        "final_report": final_report,
        "recommended_actions": intervention_result["recommended_actions"],
        "applied_actions": intervention_result["applied_actions"],
        "control_state": intervention_result["control_state"],
    }


def run_cross_consumer_long_soak(
    suites: Dict[str, List[Dict[str, Any]]],
    *,
    iterations: int = 5,
    clear_ledger: bool = True,
    threshold_profile: str | None = None,
) -> Dict[str, Any]:
    threshold_profile = resolve_profile(threshold_profile)
    if clear_ledger:
        clear_consumer_records()

    timeline: List[Dict[str, Any]] = []
    for index in range(max(1, int(iterations))):
        per_consumer: List[Dict[str, Any]] = []
        for project_type, scenarios in suites.items():
            results = run_consumer_stress(project_type, scenarios)
            per_consumer.append(
                {
                    "project_type": project_type,
                    "scenario_count": len(scenarios),
                    "ok_count": sum(1 for row in results if row.get("ok")),
                    "blocked_count": sum(1 for row in results if row.get("stage") == "consumer_control"),
                    "calibration": _calibration_summary(results, scenarios),
                }
            )
        report = consumer_operating_report()
        intervention_result = apply_interventions(report, profile=threshold_profile)
        timeline.append(
            {
                "iteration": index + 1,
                "per_consumer": per_consumer,
                "verdict_distribution": dict(report.get("verdict_distribution", {})),
                "recommended_actions": intervention_result["recommended_actions"],
                "applied_actions": intervention_result["applied_actions"],
                "control_state": intervention_result["control_state"],
            }
        )

    return {
        "iterations": max(1, int(iterations)),
        "consumers": sorted(suites),
        "threshold_profile": threshold_profile,
        "timeline": timeline,
        "final_report": consumer_operating_report(),
        "control_state": consumer_control_state(),
        "horizon_health": _horizon_health(timeline),
    }


def compare_threshold_profiles(
    suites: Dict[str, List[Dict[str, Any]]],
    *,
    iterations: int = 5,
    profiles: List[str] | None = None,
) -> Dict[str, Any]:
    profiles = list(profiles or ["balanced", "conservative", "rollout"])
    comparisons: List[Dict[str, Any]] = []
    for profile in profiles:
        result = run_cross_consumer_long_soak(
            suites,
            iterations=iterations,
            clear_ledger=True,
            threshold_profile=profile,
        )
        calibration = {
            "false_hold": 0,
            "false_reject": 0,
            "false_escalate": 0,
            "false_promote": 0,
            "labeled_cases": 0,
            "matches": 0,
            "false_hold_reasons": {},
        }
        for tick in result["timeline"]:
            for row in tick.get("per_consumer", []):
                summary = dict(row.get("calibration") or {})
                for key in ("false_hold", "false_reject", "false_escalate", "false_promote", "labeled_cases", "matches"):
                    calibration[key] += int(summary.get(key, 0) or 0)
                for reason, count in dict(summary.get("false_hold_reasons") or {}).items():
                    calibration["false_hold_reasons"][reason] = calibration["false_hold_reasons"].get(reason, 0) + int(count or 0)
        labeled = calibration["labeled_cases"] or 1
        calibration["match_rate"] = calibration["matches"] / labeled
        calibration["false_hold_reasons"] = dict(
            sorted(calibration["false_hold_reasons"].items(), key=lambda item: (-item[1], item[0]))
        )
        comparisons.append(
            {
                "profile": profile,
                "final_verdict_distribution": dict(result.get("final_report", {}).get("verdict_distribution", {})),
                "control_state": result.get("control_state"),
                "horizon_health": result.get("horizon_health", {}),
                "calibration": calibration,
            }
        )

    best = max(comparisons, key=lambda row: row["calibration"]["match_rate"]) if comparisons else None
    return {
        "iterations": iterations,
        "profiles": comparisons,
        "recommended_default_profile": None if best is None else best["profile"],
    }
