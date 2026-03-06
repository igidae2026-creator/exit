import json
import os
import tempfile
from pathlib import Path

from artifact.archive import extinction_memory, resurrection_replay, save, seed_bank_recovery
from metaos.archive.civilization_memory import remember
from metaos.runtime.memory_pressure import memory_pressure
from runtime.civilization_memory import civilization_state


def test_civilization_memory_appends_rows() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_CIVILIZATION_MEMORY"] = str(Path(tmp) / "civilization_memory.jsonl")
        os.environ["METAOS_ARCHIVE"] = str(Path(tmp) / "archive.jsonl")
        os.environ["METAOS_RESURRECTION_INDEX"] = str(Path(tmp) / "resurrection_index.jsonl")
        try:
            remember("pressure_snapshot", {"novelty_pressure": 0.7})
            save("memory", {"artifact_id": "a1"})
            rows = Path(os.environ["METAOS_CIVILIZATION_MEMORY"]).read_text(encoding="utf-8").strip().splitlines()
            payload = json.loads(rows[0])
            assert payload["kind"] == "pressure_snapshot"
            assert seed_bank_recovery("memory")
            assert extinction_memory()
            assert resurrection_replay("pressure_snapshot")
            pressure = memory_pressure()
            assert pressure["memory_growth"] > 0.0
            civ = civilization_state()
            assert civ["knowledge_density"] > 0.0
            assert civ["exploration_outcomes"]["memory_rows"] > 0
        finally:
            os.environ.pop("METAOS_CIVILIZATION_MEMORY", None)
            os.environ.pop("METAOS_ARCHIVE", None)
            os.environ.pop("METAOS_RESURRECTION_INDEX", None)
