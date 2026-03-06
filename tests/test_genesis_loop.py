import os
import tempfile
from pathlib import Path

from metaos.runtime.exploration_loop import run_loop


class _SignalSource:
    def __init__(self) -> None:
        self.calls: list[int] = []

    def safe_shutdown(self, tick: int) -> bool:
        return tick >= 3

    def signal(self, tick: int) -> dict[str, int]:
        self.calls.append(tick)
        return {"tick": tick, "value": tick}


def test_genesis_loop_runs_until_safe_shutdown() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        try:
            source = _SignalSource()
            ticks = list(run_loop(source))
            assert [tick["tick"] for tick in ticks] == [1, 2, 3]
            assert source.calls == [1, 2, 3]
            assert (root / "events.jsonl").exists()
            assert (root / "metrics.jsonl").exists()
            assert (root / "artifact_registry.jsonl").exists()
        finally:
            os.environ.pop("METAOS_ROOT", None)
