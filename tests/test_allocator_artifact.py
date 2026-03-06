import os
import tempfile
from pathlib import Path

from metaos.runtime.allocator_artifact import load_all, register_allocator_artifact


def test_allocator_artifact_registry_appends_rows() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ALLOCATOR_REGISTRY"] = str(Path(tmp) / "allocator_registry.jsonl")
        try:
            artifact_id = register_allocator_artifact(
                {"worker_budget": 8},
                {"novelty_pressure": 0.5},
                8,
                {"worker_budget": 8, "mutation_budget": 12.0},
                parent="root",
            )
            rows = load_all()
            assert artifact_id
            assert len(rows) == 1
            assert rows[0]["workers"] == 8
            assert rows[0]["parent"] == "root"
        finally:
            os.environ.pop("METAOS_ALLOCATOR_REGISTRY", None)
