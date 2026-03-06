from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from genesis.spine import append_event, append_metrics


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["METAOS_ROOT"] = str(root)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run([sys.executable, "-m", "app.cli", *args], env=env, capture_output=True, text=True, check=False, timeout=20)


def test_app_cli_status_commands_work() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        try:
            append_event("tick_started", {"tick": 1})
            append_metrics({"tick": 1, "score": 0.8, "quest": {"type": "exploration"}, "routing": {"selected_domain": "default"}})
            for command in ("civilization-status", "lineage-status", "domain-status", "health"):
                completed = _run(root, command)
                assert completed.returncode == 0, completed.stderr
                json.loads(completed.stdout)
        finally:
            os.environ.pop("METAOS_ROOT", None)
