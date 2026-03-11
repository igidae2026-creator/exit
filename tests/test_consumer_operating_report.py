from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from metaos.adapters.research_note import adapter_manifest as research_manifest
from metaos.runtime.consumer_api import (
    consumer_operating_status,
    register_consumer,
    register_consumer_migration,
    reset_consumers,
    resolve_consumer,
    run_consumer_conformance,
)


def _webnovel_manifest():
    webnovel_root = Path("/home/meta_os/web_novel")
    if str(webnovel_root) not in sys.path:
        sys.path.insert(0, str(webnovel_root))
    from engine.metaos_consumer_bridge import adapter_manifest

    return adapter_manifest


def setup_function():
    reset_consumers()


def test_consumer_operating_report_exposes_verdicts_and_migration_queue():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            register_consumer("web_novel", _webnovel_manifest())
            register_consumer("research_note", research_manifest)
            register_consumer(
                "legacy_note",
                lambda: {
                    "adapter_name": "legacy_note",
                    "contract_version": "0.8.0",
                    "material_from_source": lambda source: source,
                    "artifact_from_output": lambda artifact: artifact,
                },
            )
            register_consumer_migration(
                "0.8.0",
                "1.0.0",
                strategy="rewrite_then_replay",
                steps=["freeze writes", "migrate consumer", "resume"],
            )
            resolve_consumer("legacy_note")
            run_consumer_conformance(
                "research_note",
                {
                    "material_id": "src:research_1",
                    "quality_score": 0.92,
                    "scope_fit_score": 0.81,
                    "risk_score": 0.15,
                    "domain": "research",
                },
                {
                    "artifact_id": "artifact:research_1",
                    "quality_score": 0.9,
                    "relevance_score": 0.88,
                    "stability_score": 0.81,
                    "risk_score": 0.12,
                },
            )

            report = consumer_operating_status()
            assert "hold" in report["verdict_distribution"]
            assert "promote" in report["verdict_distribution"]
            assert report["migration_queue"]
            assert report["consumer_health_rollup"]
        finally:
            os.environ.pop("METAOS_ROOT", None)


def test_cli_consumer_status_returns_operating_report():
    with tempfile.TemporaryDirectory() as tmp:
        env = os.environ.copy()
        env["METAOS_ROOT"] = tmp
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, "-m", "app.cli", "consumer-status"],
            cwd="/home/meta_os/metaos",
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        assert completed.returncode == 0, completed.stderr
        payload = json.loads(completed.stdout)
        assert "verdict_distribution" in payload
