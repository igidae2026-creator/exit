from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliSmokeTests(unittest.TestCase):
    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def _env(self, root: Path) -> dict[str, str]:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["METAOS_RUNTIME_ROOT"] = str(root / ".metaos_runtime")
        env["METAOS_TICK_SECONDS"] = "0"
        env["METAOS_MAX_TICKS"] = "2"
        return env

    def _run(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        repo_root = self._repo_root()
        return subprocess.run([sys.executable, "-m", "metaos.cli", *args], cwd=repo_root, env=self._env(root), capture_output=True, text=True, check=False, timeout=20)

    def test_metaos_help_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            completed = self._run(Path(tmp), "--help")
            self.assertEqual(completed.returncode, 0)

    def test_metaos_validate_help_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            completed = self._run(Path(tmp), "validate", "--help")
            self.assertEqual(completed.returncode, 0)

    def test_metaos_run_once_help_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            completed = self._run(Path(tmp), "run-once", "--help")
            self.assertEqual(completed.returncode, 0)

    def test_metaos_validate_and_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            validate = self._run(root, "validate")
            self.assertEqual(validate.returncode, 0, validate.stderr)
            replay = self._run(root, "replay")
            self.assertEqual(replay.returncode, 0, replay.stderr)
            payload = json.loads(replay.stdout)
            self.assertIn("tick", payload)


if __name__ == "__main__":
    unittest.main()
