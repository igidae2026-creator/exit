from __future__ import annotations

import os
import tempfile

from metaos.adapters.research_note import adapter_manifest as research_manifest
from metaos.runtime.consumer_api import (
    consumer_operating_status,
    register_consumer,
    reset_consumers,
    run_cross_consumer_autonomous_soak,
    run_consumer_autonomous_loop,
)
from metaos.runtime.consumer_reporting import read_consumer_records


def setup_function() -> None:
    reset_consumers()


def test_autonomous_loop_bootstraps_without_seed_tasks() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            register_consumer("research_note", research_manifest)

            result = run_consumer_autonomous_loop("research_note", max_steps=1)
            report = consumer_operating_status()

            assert result["generated_tasks"] == 1
            assert result["executed_steps"] == 1
            assert result["accepted_count"] == 1
            assert report["autonomous_loop_stats"]["generated"] == 1
            assert report["autonomous_loop_stats"]["accepted"] == 1
        finally:
            os.environ.pop("METAOS_ROOT", None)


def test_autonomous_loop_records_failure_and_generates_repair_task() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            register_consumer("research_note", research_manifest)

            result = run_consumer_autonomous_loop(
                "research_note",
                max_steps=3,
                seed_tasks=[
                    {
                        "source": {
                            "material_id": "seed:research_note",
                            "quality_score": 0.92,
                            "scope_fit_score": 0.9,
                            "risk_score": 0.12,
                            "domain": "research",
                        },
                        "artifact_input": {
                            "artifact_id": "seed:research_note",
                            "quality_score": 0.79,
                            "relevance_score": 0.74,
                            "stability_score": 0.7,
                            "risk_score": 0.18,
                        },
                    }
                ],
            )
            records = read_consumer_records()
            report = consumer_operating_status()

            assert result["failed_count"] >= 1
            assert result["accepted_count"] >= 1
            assert any(row["record_type"] == "autonomous_task_failed" for row in records)
            assert any(row["record_type"] == "autonomous_task_generated" and row["payload"].get("strategy") == "repair" for row in records)
            assert report["autonomous_loop_stats"]["failed"] >= 1
            assert report["autonomous_loop_stats"]["accepted"] >= 1
            assert result["accepted_strategy_distribution"]["repair"] >= 1
            assert result["next_seed_task"] is not None
            assert result["next_seed_task"]["artifact_input"]["quality_score"] >= 0.88
        finally:
            os.environ.pop("METAOS_ROOT", None)


def test_autonomous_loop_stops_on_unrecoverable_missing_adapter() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            result = run_consumer_autonomous_loop(
                "missing_project",
                max_steps=3,
                seed_tasks=[
                    {
                        "source": {"material_id": "missing", "quality_score": 0.9, "scope_fit_score": 0.9, "risk_score": 0.1},
                        "artifact_input": {"artifact_id": "missing", "quality_score": 0.9, "relevance_score": 0.9, "stability_score": 0.9, "risk_score": 0.1},
                    }
                ],
            )

            assert result["failed_count"] == 1
            assert result["accepted_count"] == 0
            assert result["pending_tasks"] == []
            assert result["failure_reasons"]["missing_project_adapter"] == 1
        finally:
            os.environ.pop("METAOS_ROOT", None)


def test_cross_consumer_autonomous_soak_tracks_accept_and_repair_rates() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            register_consumer("research_note", research_manifest)
            result = run_cross_consumer_autonomous_soak(
                {
                    "research_note": [
                        {
                            "source": {
                                "material_id": "seed:research_note",
                                "quality_score": 0.92,
                                "scope_fit_score": 0.9,
                                "risk_score": 0.12,
                                "domain": "research",
                            },
                            "artifact_input": {
                                "artifact_id": "seed:research_note",
                                "quality_score": 0.79,
                                "relevance_score": 0.74,
                                "stability_score": 0.7,
                                "risk_score": 0.18,
                            },
                        }
                    ],
                    "missing_project": None,
                },
                iterations=2,
                max_steps=3,
            )
            report = consumer_operating_status()

            assert result["iterations"] == 2
            assert len(result["timeline"]) == 2
            assert result["autonomous_health"]["mean_accept_rate"] > 0.0
            assert report["autonomous_loop_stats"]["executed"] >= 2
            assert report["autonomous_loop_stats"]["mean_accept_rate"] > 0.0
            assert result["timeline"][0]["per_consumer"][0]["next_seed_task"] is not None
        finally:
            os.environ.pop("METAOS_ROOT", None)
