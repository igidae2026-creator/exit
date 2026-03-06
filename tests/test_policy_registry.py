import os
import tempfile
from pathlib import Path

from metaos.policy.policy_registry import load_all, register_policy


def test_policy_registry_appends_policy_artifacts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_POLICY_REGISTRY"] = str(Path(tmp) / "policy_registry.jsonl")
        try:
            artifact_id = register_policy({"mutation_rate": 0.2}, {"novelty_pressure": 0.8}, 0.75, parent="root")
            rows = load_all()
            assert artifact_id
            assert len(rows) == 1
            assert rows[0]["parent"] == "root"
            assert rows[0]["policy"]["mutation_rate"] == 0.2
        finally:
            os.environ.pop("METAOS_POLICY_REGISTRY", None)
