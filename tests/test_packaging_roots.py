from pathlib import Path


def test_pyproject_includes_all_runtime_roots() -> None:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    for package in ("observer*", "signal*", "strategy*", "ecosystem*", "federation*"):
        assert package in text


def test_setup_includes_runtime_roots() -> None:
    text = Path("setup.py").read_text(encoding="utf-8")
    for package in ("observer*", "signal*", "strategy*", "ecosystem*", "federation*"):
        assert package in text
