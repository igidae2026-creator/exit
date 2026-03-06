from pathlib import Path


def test_orchestrator_is_thin() -> None:
    path = Path("runtime/oed_orchestrator.py")
    assert len(path.read_text(encoding="utf-8").splitlines()) <= 170
