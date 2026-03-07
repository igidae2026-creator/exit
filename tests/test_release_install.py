from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, check=False, timeout=timeout)


def test_built_wheel_installs_and_runs_public_cli() -> None:
    repo = Path(".").resolve()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        wheel_dir = root / "wheelhouse"
        wheel_dir.mkdir()
        built = _run([sys.executable, "-m", "pip", "wheel", ".", "--no-build-isolation", "--no-deps", "-w", str(wheel_dir)], cwd=repo, timeout=240)
        assert built.returncode == 0, built.stderr
        wheels = sorted(wheel_dir.glob("metaos-*.whl"))
        assert wheels
        venv_dir = root / "venv"
        created = _run([sys.executable, "-m", "venv", str(venv_dir)], cwd=repo)
        assert created.returncode == 0, created.stderr
        python = venv_dir / "bin" / "python"
        installed = _run([str(python), "-m", "pip", "install", "--no-deps", str(wheels[-1])], cwd=repo, timeout=240)
        assert installed.returncode == 0, installed.stderr
        env = os.environ.copy()
        env["METAOS_ROOT"] = str(root / "runtime")
        json_commands = (
            ["-m", "app.cli", "health"],
            ["-m", "app.cli", "replay-check"],
            ["-m", "metaos.cli", "civilization-status"],
            ["-m", "metaos.cli", "lineage-status"],
            ["-m", "metaos.cli", "domain-status"],
            ["-m", "metaos.cli", "pressure-status"],
            ["-m", "metaos.cli", "economy-status"],
            ["-m", "metaos.cli", "stability-status"],
            ["-m", "metaos.cli", "safety-status"],
            ["-m", "metaos.cli", "long-run-check", "--ticks", "4"],
        )
        for command in json_commands:
            completed = _run([str(python), *command], cwd=repo, env=env)
            assert completed.returncode == 0, completed.stderr
            json.loads(completed.stdout)
        validate_release = _run([str(python), "-m", "metaos.cli", "validate-release"], cwd=repo, env=env)
        assert validate_release.returncode == 0, validate_release.stderr


def test_release_zip_matches_manifest_and_contains_metadata() -> None:
    repo = Path(".").resolve()
    build = _run(["bash", "scripts/build_release_zip.sh"], cwd=repo, timeout=240)
    assert build.returncode == 0, build.stderr
    zip_path = Path(build.stdout.strip().splitlines()[-1])
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        for required in ("pyproject.toml", "setup.py", "README.md", "RUNBOOK.md", "validation/ownership_manifest.json", "metaos/cli.py"):
            assert required in names, required
