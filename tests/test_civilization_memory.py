import json
import os
import tempfile
from pathlib import Path

from metaos.archive.civilization_memory import remember


def test_civilization_memory_appends_rows() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_CIVILIZATION_MEMORY"] = str(Path(tmp) / "civilization_memory.jsonl")
        try:
            remember("pressure_snapshot", {"novelty_pressure": 0.7})
            rows = Path(os.environ["METAOS_CIVILIZATION_MEMORY"]).read_text(encoding="utf-8").strip().splitlines()
            payload = json.loads(rows[0])
            assert payload["kind"] == "pressure_snapshot"
        finally:
            os.environ.pop("METAOS_CIVILIZATION_MEMORY", None)
