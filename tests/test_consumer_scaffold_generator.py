import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from metaos.runtime.adapter_scaffold import generate_consumer_scaffold


def test_generate_consumer_scaffold_writes_expected_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        payload = generate_consumer_scaffold(tmp, "analytics_dash")
        assert Path(payload["adapter_path"]).exists()
        assert Path(payload["test_path"]).exists()
        assert Path(payload["doc_path"]).exists()


def test_cli_generate_consumer_scaffold_command() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, "-m", "app.cli", "generate-consumer-scaffold", "analytics_dash", "--output-root", tmp],
            cwd="/home/meta_os/metaos",
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        assert completed.returncode == 0, completed.stderr
        payload = json.loads(completed.stdout)
        assert Path(payload["adapter_path"]).exists()
