from __future__ import annotations

from typing import Any, Callable, Dict

from metaos.runtime.adapter_conformance import run_adapter_conformance
from metaos.runtime.adapter_migrations import clear_migration_rules, migration_plan, register_migration_rule
from metaos.runtime.adapter_registry import (
    adapter_resolution,
    clear_registered_adapters,
    conformance_matrix,
    register_adapter,
)
from metaos.runtime.consumer_control import (
    consumer_control_decision,
    consumer_control_state,
    projected_queue_state,
    projected_supervisor_state,
)
from metaos.runtime.consumer_interventions import apply_interventions, default_profile_for_consumer, resolve_profile
from metaos.runtime.consumer_reporting import append_consumer_record, consumer_operating_report


AdapterFactory = Callable[[], Dict[str, Any]]


def register_consumer(project_type: str, factory: AdapterFactory) -> None:
    register_adapter(project_type, factory)


def reset_consumers() -> None:
    clear_registered_adapters()
    clear_migration_rules()


def resolve_consumer(project_type: str) -> Dict[str, Any]:
    resolution = adapter_resolution(project_type)
    append_consumer_record(
        "consumer_resolution",
        {
            "project_type": project_type,
            "verdict": resolution.get("verdict"),
            "reason": resolution.get("reason"),
            "status": resolution.get("status"),
        },
    )
    return resolution


def consumer_matrix() -> list[dict]:
    rows = conformance_matrix()
    for row in rows:
        row["default_profile"] = default_profile_for_consumer(row.get("project_type"))
    return rows


def run_consumer_conformance(project_type: str, source: Dict[str, Any], artifact_input: Dict[str, Any]) -> Dict[str, Any]:
    control = consumer_control_decision(project_type)
    if not control.get("allowed", True):
        active_job_id = f"control:{project_type}"
        result = {
            "ok": False,
            "stage": "consumer_control",
            "resolution": {
                "project_type": project_type,
                "verdict": control.get("verdict"),
                "reason": control.get("reason"),
                "status": "blocked_by_control_state",
            },
            "control_state": control.get("state"),
            "queue_state": projected_queue_state(project_type, active_job_id=active_job_id),
            "supervisor_state": projected_supervisor_state(project_type, active_job_id=active_job_id),
        }
        append_consumer_record(
            "consumer_control_gate",
            {
                "project_type": project_type,
                "verdict": control.get("verdict"),
                "reason": control.get("reason"),
                "status": "blocked_by_control_state",
            },
        )
        append_consumer_record(
            "consumer_conformance",
            {
                "project_type": project_type,
                "verdict": control.get("verdict", "hold"),
                "reason": control.get("reason") or "consumer_control",
                "ok": False,
            },
        )
        return result

    result = run_adapter_conformance(project_type, source, artifact_input)
    if result.get("ok"):
        append_consumer_record(
            "consumer_conformance",
            {
                "project_type": project_type,
                "verdict": result.get("promotion_decision", {}).get("verdict", result.get("scope_decision", {}).get("verdict")),
                "reason": result.get("promotion_decision", {}).get("reason", result.get("scope_decision", {}).get("reason")),
                "ok": True,
            },
        )
    else:
        resolution = result.get("resolution", {})
        append_consumer_record(
            "consumer_conformance",
            {
                "project_type": project_type,
                "verdict": resolution.get("verdict", "hold"),
                "reason": result.get("reason") or resolution.get("reason") or result.get("stage"),
                "ok": False,
            },
        )
    return result


def register_consumer_migration(
    from_version: str,
    to_version: str,
    *,
    strategy: str,
    steps: list[str],
    compatibility_window: str = "bounded",
) -> None:
    register_migration_rule(
        from_version,
        to_version,
        strategy=strategy,
        steps=list(steps),
        compatibility_window=compatibility_window,
    )
    append_consumer_record(
        "consumer_migration",
        {
            "from_version": from_version,
            "to_version": to_version,
            "strategy": strategy,
            "compatibility_window": compatibility_window,
        },
    )


def consumer_migration_plan(from_version: str, to_version: str) -> Dict[str, Any]:
    return migration_plan(from_version, to_version)


def consumer_operating_status() -> Dict[str, Any]:
    report = consumer_operating_report()
    report["control_state"] = consumer_control_state()
    return report


def run_consumer_stress(
    project_type: str,
    scenarios: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results = []
    for scenario in scenarios:
        results.append(
            run_consumer_conformance(
                project_type,
                dict(scenario.get("source") or {}),
                dict(scenario.get("artifact_input") or {}),
            )
        )
    return results


def apply_consumer_interventions(*, profile: str | None = None, project_type: str | None = None) -> Dict[str, Any]:
    return apply_interventions(
        consumer_operating_report(),
        profile=resolve_profile(profile, project_type=project_type),
        project_type=project_type,
    )


def run_cross_consumer_long_soak(
    suites: dict[str, list[dict[str, Any]]],
    *,
    iterations: int = 5,
    clear_ledger: bool = True,
    threshold_profile: str | None = None,
) -> Dict[str, Any]:
    from metaos.runtime.consumer_soak import run_cross_consumer_long_soak as _run_cross_consumer_long_soak

    return _run_cross_consumer_long_soak(
        suites,
        iterations=iterations,
        clear_ledger=clear_ledger,
        threshold_profile=threshold_profile,
    )


def run_consumer_soak_suite(
    project_type: str,
    scenarios: list[dict[str, Any]],
    *,
    iterations: int = 3,
    clear_ledger: bool = True,
    threshold_profile: str | None = None,
) -> Dict[str, Any]:
    from metaos.runtime.consumer_soak import run_consumer_soak_suite as _run_consumer_soak_suite

    return _run_consumer_soak_suite(
        project_type,
        scenarios,
        iterations=iterations,
        clear_ledger=clear_ledger,
        threshold_profile=threshold_profile,
    )


def compare_consumer_threshold_profiles(
    suites: dict[str, list[dict[str, Any]]],
    *,
    iterations: int = 5,
    profiles: list[str] | None = None,
) -> Dict[str, Any]:
    from metaos.runtime.consumer_soak import compare_threshold_profiles as _compare_threshold_profiles

    return _compare_threshold_profiles(
        suites,
        iterations=iterations,
        profiles=profiles,
    )
