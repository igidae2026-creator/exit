import subprocess


def test_release_tree_validator_exits_zero() -> None:
    completed = subprocess.run(["bash", "scripts/validate_release_tree.sh"], capture_output=True, text=True, check=False, timeout=20)
    assert completed.returncode == 0, completed.stderr
