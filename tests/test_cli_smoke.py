from __future__ import annotations

import subprocess
import sys


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "metaos.cli", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_metaos_help_exits_zero() -> None:
    completed = _run("--help")
    assert completed.returncode == 0


def test_metaos_validate_help_exits_zero() -> None:
    completed = _run("validate", "--help")
    assert completed.returncode == 0


def test_metaos_run_once_help_exits_zero() -> None:
    completed = _run("run-once", "--help")
    assert completed.returncode == 0


def test_metaos_validate_defaults_does_not_hang() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "metaos.cli", "validate"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert completed.returncode in {0, 2}
