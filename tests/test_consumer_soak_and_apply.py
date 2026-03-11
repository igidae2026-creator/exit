from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from metaos.adapters.analytics_dash import adapter_manifest as analytics_manifest
from metaos.adapters.code_patch import adapter_manifest as code_patch_manifest
from metaos.adapters.research_note import adapter_manifest as research_manifest
from metaos.runtime.consumer_api import (
    compare_consumer_threshold_profiles,
    register_consumer,
    reset_consumers,
    run_consumer_conformance,
    run_consumer_soak_suite,
    run_cross_consumer_long_soak,
)
from metaos.runtime.consumer_control import consumer_control_state
from metaos.runtime.consumer_interventions import apply_interventions
from metaos.runtime.consumer_reporting import read_consumer_records


def setup_function():
    reset_consumers()


def _stress_scenarios():
    return [
        {
            "source": {"material_id": "a", "quality_score": 0.72, "scope_fit_score": 0.7, "risk_score": 0.42},
            "artifact_input": {"artifact_id": "a", "quality_score": 0.6, "relevance_score": 0.7, "stability_score": 0.7, "risk_score": 0.4},
            "expected_verdict": "hold",
        },
        {
            "source": {"material_id": "b", "quality_score": 0.92, "scope_fit_score": 0.92, "risk_score": 0.18},
            "artifact_input": {"artifact_id": "b", "quality_score": 0.3, "relevance_score": 0.3, "stability_score": 0.5, "risk_score": 0.75},
            "expected_verdict": "reject",
        },
        {
            "source": {"material_id": "c", "quality_score": 0.95, "scope_fit_score": 0.95, "risk_score": 0.95},
            "artifact_input": {"artifact_id": "c", "quality_score": 0.95, "relevance_score": 0.95, "stability_score": 0.95, "risk_score": 0.95},
            "expected_verdict": "escalate",
        },
    ]


def _analytics_scenarios():
    return [
        {
            "source": {"material_id": "dash-a", "quality_score": 0.91, "scope_fit_score": 0.9, "risk_score": 0.18},
            "artifact_input": {"artifact_id": "dash-a", "quality_score": 0.93, "relevance_score": 0.9, "stability_score": 0.88, "risk_score": 0.18},
            "expected_verdict": "promote",
        },
        {
            "source": {"material_id": "dash-b", "quality_score": 0.82, "scope_fit_score": 0.8, "risk_score": 0.94},
            "artifact_input": {"artifact_id": "dash-b", "quality_score": 0.9, "relevance_score": 0.9, "stability_score": 0.9, "risk_score": 0.94},
            "expected_verdict": "escalate",
        },
    ]


def _code_patch_scenarios():
    return [
        {
            "source": {"material_id": "patch-a", "quality_score": 0.92, "scope_fit_score": 0.9, "risk_score": 0.18},
            "artifact_input": {"artifact_id": "patch-a", "quality_score": 0.2, "relevance_score": 0.2, "stability_score": 0.4, "risk_score": 0.8},
            "expected_verdict": "reject",
        },
        {
            "source": {"material_id": "patch-b", "quality_score": 0.91, "scope_fit_score": 0.91, "risk_score": 0.18},
            "artifact_input": {"artifact_id": "patch-b", "quality_score": 0.25, "relevance_score": 0.25, "stability_score": 0.45, "risk_score": 0.82},
            "expected_verdict": "reject",
        },
    ]


def _boundary_research_scenarios():
    return [
        {
            "source": {"material_id": "br-1", "quality_score": 0.74, "scope_fit_score": 0.74, "risk_score": 0.36},
            "artifact_input": {"artifact_id": "br-1", "quality_score": 0.72, "relevance_score": 0.73, "stability_score": 0.72, "risk_score": 0.36},
            "expected_verdict": "hold",
        },
        {
            "source": {"material_id": "br-2", "quality_score": 0.74, "scope_fit_score": 0.74, "risk_score": 0.36},
            "artifact_input": {"artifact_id": "br-2", "quality_score": 0.9, "relevance_score": 0.88, "stability_score": 0.82, "risk_score": 0.2},
            "expected_verdict": "hold",
        },
        {
            "source": {"material_id": "br-3", "quality_score": 0.91, "scope_fit_score": 0.9, "risk_score": 0.18},
            "artifact_input": {"artifact_id": "br-3", "quality_score": 0.92, "relevance_score": 0.9, "stability_score": 0.87, "risk_score": 0.18},
            "expected_verdict": "promote",
        },
    ]


def _boundary_analytics_scenarios():
    return [
        {
            "source": {"material_id": "ba-1", "quality_score": 0.91, "scope_fit_score": 0.9, "risk_score": 0.16},
            "artifact_input": {"artifact_id": "ba-1", "quality_score": 0.91, "relevance_score": 0.88, "stability_score": 0.85, "risk_score": 0.16},
            "expected_verdict": "promote",
        },
        {
            "source": {"material_id": "ba-2", "quality_score": 0.91, "scope_fit_score": 0.9, "risk_score": 0.16},
            "artifact_input": {"artifact_id": "ba-2", "quality_score": 0.89, "relevance_score": 0.86, "stability_score": 0.82, "risk_score": 0.16},
            "expected_verdict": "promote",
        },
        {
            "source": {"material_id": "ba-3", "quality_score": 0.91, "scope_fit_score": 0.9, "risk_score": 0.16},
            "artifact_input": {"artifact_id": "ba-3", "quality_score": 0.9, "relevance_score": 0.88, "stability_score": 0.83, "risk_score": 0.16},
            "expected_verdict": "promote",
        },
        {
            "source": {"material_id": "ba-4", "quality_score": 0.95, "scope_fit_score": 0.94, "risk_score": 0.16},
            "artifact_input": {"artifact_id": "ba-4", "quality_score": 0.95, "relevance_score": 0.94, "stability_score": 0.91, "risk_score": 0.95},
            "expected_verdict": "escalate",
        },
    ]


def _boundary_code_patch_scenarios():
    return [
        {
            "source": {"material_id": "bc-1", "quality_score": 0.92, "scope_fit_score": 0.9, "risk_score": 0.18},
            "artifact_input": {"artifact_id": "bc-1", "quality_score": 0.44, "relevance_score": 0.44, "stability_score": 0.6, "risk_score": 0.71},
            "expected_verdict": "hold",
        },
        {
            "source": {"material_id": "bc-2", "quality_score": 0.92, "scope_fit_score": 0.9, "risk_score": 0.18},
            "artifact_input": {"artifact_id": "bc-2", "quality_score": 0.43, "relevance_score": 0.43, "stability_score": 0.58, "risk_score": 0.73},
            "expected_verdict": "reject",
        },
        {
            "source": {"material_id": "bc-3", "quality_score": 0.92, "scope_fit_score": 0.9, "risk_score": 0.18},
            "artifact_input": {"artifact_id": "bc-3", "quality_score": 0.44, "relevance_score": 0.43, "stability_score": 0.57, "risk_score": 0.73},
            "expected_verdict": "reject",
        },
    ]


def _webnovel_manifest():
    webnovel_root = Path("/home/meta_os/web_novel")
    if str(webnovel_root) not in sys.path:
        sys.path.insert(0, str(webnovel_root))
    from engine.metaos_consumer_bridge import adapter_manifest

    return adapter_manifest


def _boundary_webnovel_scenarios():
    return [
        {
            "source": {
                "project": {"platform": "Munpia", "genre_bucket": "A"},
                "track": {"id": "boundary_1"},
                "material_id": "src:boundary_1",
                "quality_score": 0.82,
                "scope_fit_score": 0.8,
                "risk_score": 0.18,
            },
            "artifact_input": {
                "cfg": {"project": {"platform": "Munpia", "genre_bucket": "A"}},
                "episode_result": {
                    "episode": 11,
                    "predicted_retention": 0.87,
                    "quality_score": 0.84,
                    "quality_gate": {"passed": True, "failed_checks": []},
                    "story_state": {"world": {"instability": 2}},
                },
            },
            "expected_verdict": "promote",
        },
        {
            "source": {
                "project": {"platform": "Munpia", "genre_bucket": "A"},
                "track": {"id": "boundary_2"},
                "material_id": "src:boundary_2",
                "quality_score": 0.82,
                "scope_fit_score": 0.8,
                "risk_score": 0.18,
            },
            "artifact_input": {
                "cfg": {"project": {"platform": "Munpia", "genre_bucket": "A"}},
                "episode_result": {
                    "episode": 12,
                    "predicted_retention": 0.44,
                    "quality_score": 0.39,
                    "quality_gate": {"passed": False, "failed_checks": ["payoff_integrity"]},
                    "story_state": {"world": {"instability": 5}},
                },
            },
            "expected_verdict": "reject",
        },
    ]


def test_apply_interventions_records_append_only_actions():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            payload = apply_interventions(
                {
                    "verdict_distribution": {"hold": 5, "reject": 4, "escalate": 3, "promote": 2},
                    "hold_top_reasons": [("migration_required", 3)],
                    "reject_top_patterns": [("not_promotion_worthy", 4)],
                    "escalate_rate": 0.25,
                    "migration_queue": [{"from_version": "0.8.0", "to_version": "1.0.0"}],
                    "consumer_health_rollup": [
                        {"project_type": "research_note", "hold_rate": 0.5, "reject_rate": 0.1, "escalate_rate": 0.0},
                        {"project_type": "code_patch", "hold_rate": 0.1, "reject_rate": 0.5, "escalate_rate": 0.25},
                    ],
                    "conformance_matrix": [],
                }
            )

            records = read_consumer_records()

            assert payload["applied_actions"]
            assert any(row["record_type"] == "consumer_intervention" for row in records)
            assert all(row["payload"]["status"] == "applied" for row in records if row["record_type"] == "consumer_intervention")
        finally:
            os.environ.pop("METAOS_ROOT", None)


def test_consumer_soak_suite_runs_iterations_and_applies_actions():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            register_consumer("research_note", research_manifest)
            payload = run_consumer_soak_suite(
                "research_note",
                _stress_scenarios(),
                iterations=2,
            )

            assert payload["iterations"] == 2
            assert len(payload["per_iteration"]) == 2
            assert payload["final_report"]["verdict_distribution"]
            assert payload["applied_actions"]
            assert "control_state" in payload
            assert payload["per_iteration"][0]["calibration"]["labeled_cases"] == 3
            assert payload["threshold_profile"] == "conservative"
        finally:
            os.environ.pop("METAOS_ROOT", None)


def test_apply_interventions_changes_future_state_transitions():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            register_consumer("code_patch", code_patch_manifest)
            apply_interventions(
                {
                    "verdict_distribution": {"reject": 5},
                    "hold_top_reasons": [],
                    "reject_top_patterns": [("not_promotion_worthy", 5)],
                    "escalate_rate": 0.0,
                    "migration_queue": [],
                    "consumer_health_rollup": [
                        {"project_type": "code_patch", "hold_rate": 0.0, "reject_rate": 0.6, "escalate_rate": 0.0},
                    ],
                    "conformance_matrix": [],
                }
            )

            blocked = run_consumer_conformance(
                "code_patch",
                {"material_id": "after", "quality_score": 0.95, "scope_fit_score": 0.95, "risk_score": 0.1},
                {"artifact_id": "after", "quality_score": 0.95, "relevance_score": 0.95, "stability_score": 0.95, "risk_score": 0.1},
            )

            assert blocked["ok"] is False
            assert blocked["stage"] == "consumer_control"
            assert blocked["resolution"]["reason"] == "consumer_sandboxed"
            assert blocked["queue_state"]["queue_status"] == "blocked"
            assert blocked["supervisor_state"]["status"] == "blocked"
        finally:
            os.environ.pop("METAOS_ROOT", None)


def test_inspection_pending_is_monitor_only_not_hard_hold():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            register_consumer("research_note", research_manifest)
            apply_interventions(
                {
                    "verdict_distribution": {"hold": 5},
                    "hold_top_reasons": [("borderline_candidate", 5)],
                    "reject_top_patterns": [],
                    "escalate_rate": 0.0,
                    "migration_queue": [],
                    "consumer_health_rollup": [
                        {"project_type": "research_note", "hold_rate": 0.6, "reject_rate": 0.0, "escalate_rate": 0.0},
                    ],
                    "conformance_matrix": [],
                }
            )

            result = run_consumer_conformance(
                "research_note",
                {"material_id": "ok", "quality_score": 0.95, "scope_fit_score": 0.9, "risk_score": 0.1},
                {"artifact_id": "ok", "quality_score": 0.95, "relevance_score": 0.95, "stability_score": 0.95, "risk_score": 0.1},
            )

            assert result["ok"] is True
        finally:
            os.environ.pop("METAOS_ROOT", None)


def test_cross_consumer_long_soak_closes_loop_into_control_state():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            register_consumer("research_note", research_manifest)
            register_consumer("analytics_dash", analytics_manifest)
            register_consumer("code_patch", code_patch_manifest)

            payload = run_cross_consumer_long_soak(
                {
                    "research_note": _stress_scenarios(),
                    "analytics_dash": _analytics_scenarios(),
                    "code_patch": _code_patch_scenarios(),
                },
                iterations=2,
            )

            state = consumer_control_state()

            assert payload["timeline"]
            assert payload["final_report"]["verdict_distribution"]
            assert state["global"]["rollout_state"] == "paused"
            assert state["consumers"]["code_patch"]["operating_state"] == "sandboxed"
            assert payload["timeline"][0]["per_consumer"][0]["calibration"]["labeled_cases"] > 0
            assert "horizon_health" in payload
        finally:
            os.environ.pop("METAOS_ROOT", None)


def test_compare_threshold_profiles_returns_profile_ranking():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            register_consumer("research_note", research_manifest)
            register_consumer("analytics_dash", analytics_manifest)
            register_consumer("code_patch", code_patch_manifest)

            payload = compare_consumer_threshold_profiles(
                {
                    "research_note": _stress_scenarios(),
                    "analytics_dash": _analytics_scenarios(),
                    "code_patch": _code_patch_scenarios(),
                },
                iterations=2,
                profiles=["balanced", "conservative", "rollout"],
            )

            assert len(payload["profiles"]) == 3
            assert payload["recommended_default_profile"] in {"balanced", "conservative", "rollout"}
            assert all("match_rate" in row["calibration"] for row in payload["profiles"])
            assert all("false_hold_reasons" in row["calibration"] for row in payload["profiles"])
            assert all("horizon_health" in row for row in payload["profiles"])
        finally:
            os.environ.pop("METAOS_ROOT", None)


def test_boundary_suite_splits_profile_control_states():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            register_consumer("research_note", research_manifest)
            register_consumer("analytics_dash", analytics_manifest)
            register_consumer("code_patch", code_patch_manifest)

            payload = compare_consumer_threshold_profiles(
                {
                    "research_note": _boundary_research_scenarios(),
                    "analytics_dash": _boundary_analytics_scenarios(),
                    "code_patch": _boundary_code_patch_scenarios(),
                },
                iterations=1,
                profiles=["conservative", "rollout"],
            )

            profiles = {row["profile"]: row for row in payload["profiles"]}

            assert profiles["conservative"]["control_state"]["consumers"]["research_note"]["operating_state"] == "inspection_pending"
            assert "research_note" not in profiles["rollout"]["control_state"]["consumers"]
            assert profiles["conservative"]["control_state"]["global"]["rollout_state"] == "open"
            assert profiles["rollout"]["control_state"]["global"]["rollout_state"] == "open"
            assert profiles["conservative"]["control_state"]["consumers"]["code_patch"]["operating_state"] == "sandboxed"
            assert profiles["rollout"]["control_state"]["consumers"]["code_patch"]["operating_state"] == "sandboxed"
        finally:
            os.environ.pop("METAOS_ROOT", None)


def test_webnovel_uses_balanced_default_profile_in_boundary_soak():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            register_consumer("web_novel", _webnovel_manifest())
            payload = run_consumer_soak_suite(
                "web_novel",
                _boundary_webnovel_scenarios(),
                iterations=1,
            )

            assert payload["threshold_profile"] == "balanced"
            assert payload["per_iteration"][0]["calibration"]["labeled_cases"] == 2
        finally:
            os.environ.pop("METAOS_ROOT", None)


def test_cli_consumer_apply_interventions_returns_payload():
    with tempfile.TemporaryDirectory() as tmp:
        env = os.environ.copy()
        env["METAOS_ROOT"] = tmp
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, "-m", "app.cli", "consumer-apply-interventions"],
            cwd="/home/meta_os/metaos",
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        assert completed.returncode == 0, completed.stderr
        payload = json.loads(completed.stdout)
        assert "applied_actions" in payload
