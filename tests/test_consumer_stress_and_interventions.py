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
    register_consumer,
    register_consumer_migration,
    reset_consumers,
    run_consumer_stress,
)
from metaos.runtime.consumer_interventions import (
    default_profile_for_consumer,
    recommended_interventions,
    resolve_profile,
    threshold_profile,
)
from metaos.runtime.consumer_reporting import consumer_operating_report


def _webnovel_manifest():
    webnovel_root = Path("/home/meta_os/web_novel")
    if str(webnovel_root) not in sys.path:
        sys.path.insert(0, str(webnovel_root))
    from engine.metaos_consumer_bridge import adapter_manifest

    return adapter_manifest


def setup_function():
    reset_consumers()


def test_consumer_stress_injection_records_hold_reject_and_escalate():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            register_consumer("research_note", research_manifest)
            run_consumer_stress(
                "research_note",
                [
                    {
                        "source": {"material_id": "a", "quality_score": 0.7, "scope_fit_score": 0.7, "risk_score": 0.4},
                        "artifact_input": {"artifact_id": "a", "quality_score": 0.6, "relevance_score": 0.7, "stability_score": 0.7, "risk_score": 0.4},
                    },
                    {
                        "source": {"material_id": "b", "quality_score": 0.9, "scope_fit_score": 0.9, "risk_score": 0.2},
                        "artifact_input": {"artifact_id": "b", "quality_score": 0.3, "relevance_score": 0.3, "stability_score": 0.5, "risk_score": 0.75},
                    },
                    {
                        "source": {"material_id": "c", "quality_score": 0.9, "scope_fit_score": 0.9, "risk_score": 0.95},
                        "artifact_input": {"artifact_id": "c", "quality_score": 0.9, "relevance_score": 0.9, "stability_score": 0.9, "risk_score": 0.95},
                    },
                ],
            )
            report = consumer_operating_report()
            assert "hold" in report["verdict_distribution"] or report["hold_top_reasons"]
            assert "reject" in report["verdict_distribution"] or report["reject_top_patterns"]
            assert report["escalate_rate"] > 0.0
        finally:
            os.environ.pop("METAOS_ROOT", None)


def test_interventions_are_recommended_from_operating_report():
    report = {
        "verdict_distribution": {"hold": 5, "reject": 4, "escalate": 3, "promote": 2},
        "hold_top_reasons": [("migration_required", 3)],
        "reject_top_patterns": [("not_promotion_worthy", 4)],
        "escalate_rate": 0.21,
        "migration_queue": [{"from_version": "0.8.0", "to_version": "1.0.0"}],
        "consumer_health_rollup": [
            {"project_type": "research_note", "hold_rate": 0.5, "reject_rate": 0.1, "escalate_rate": 0.0},
            {"project_type": "code_patch", "hold_rate": 0.1, "reject_rate": 0.5, "escalate_rate": 0.25},
        ],
        "conformance_matrix": [],
    }

    actions = recommended_interventions(report)

    assert any(action["action"] == "pause_new_rollouts" for action in actions)
    assert any(action["action"] == "drain_migration_queue" for action in actions)
    assert any(action["action"] == "inspect_consumer" and action["project_type"] == "research_note" for action in actions)
    assert any(action["action"] == "sandbox_consumer" and action["project_type"] == "code_patch" for action in actions)
    assert any(action["action"] == "require_human_review" and action["project_type"] == "code_patch" for action in actions)


def test_threshold_profiles_shift_sensitivity():
    report = {
        "verdict_distribution": {"hold": 2, "reject": 2, "escalate": 1, "promote": 5},
        "hold_top_reasons": [],
        "reject_top_patterns": [],
        "escalate_rate": 0.16,
        "migration_queue": [],
        "consumer_health_rollup": [
            {"project_type": "research_note", "hold_rate": 0.34, "reject_rate": 0.31, "escalate_rate": 0.16},
        ],
        "conformance_matrix": [],
    }

    conservative = recommended_interventions(report, profile="conservative")
    rollout = recommended_interventions(report, profile="rollout")

    assert threshold_profile("conservative")["consumer_hold_rate"] < threshold_profile("rollout")["consumer_hold_rate"]
    assert any(action["action"] == "pause_new_rollouts" for action in conservative)
    assert any(action["action"] == "inspect_consumer" for action in conservative)
    assert not any(action["action"] == "pause_new_rollouts" for action in rollout)


def test_consumer_default_profile_mapping_is_policy():
    assert default_profile_for_consumer("research_note") == "conservative"
    assert default_profile_for_consumer("code_patch") == "balanced"
    assert default_profile_for_consumer("analytics_dash") == "balanced"
    assert resolve_profile(None, project_type="research_note") == "conservative"
    assert resolve_profile(None, project_type="unknown_consumer") == "balanced"


def test_cli_consumer_interventions_returns_payload():
    with tempfile.TemporaryDirectory() as tmp:
        env = os.environ.copy()
        env["METAOS_ROOT"] = tmp
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, "-m", "app.cli", "consumer-interventions"],
            cwd="/home/meta_os/metaos",
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        assert completed.returncode == 0, completed.stderr
        payload = json.loads(completed.stdout)
        assert "recommended_actions" in payload
