from __future__ import annotations

import json
import os
import subprocess
import sys

from metaos.runtime.consumer_api import consumer_migration_plan, register_consumer_migration, reset_consumers


def setup_function():
    reset_consumers()


def test_consumer_migration_plan_reports_registered_rule():
    register_consumer_migration(
        "0.9.0",
        "1.0.0",
        strategy="dual_read",
        steps=["pause consumer", "migrate adapter", "resume consumer"],
    )

    payload = consumer_migration_plan("0.9.0", "1.0.0")

    assert payload["available"] is True
    assert payload["strategy"] == "dual_read"


def test_cli_consumer_migration_plan_returns_nonzero_without_rule():
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-m", "app.cli", "consumer-migration-plan", "0.8.0", "1.0.0"],
        cwd="/home/meta_os/metaos",
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )

    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["available"] is False
