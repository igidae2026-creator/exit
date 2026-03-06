import os
import tempfile
from pathlib import Path

from metaos.policy.evaluation_artifact import load_all, register_evaluation
from metaos.policy.evolve_evaluation import evolve_evaluation


def test_evaluation_artifact_appends_jsonl_rows() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_EVALUATION_REGISTRY"] = str(Path(tmp) / "evaluation_registry.jsonl")
        try:
            evaluation = evolve_evaluation(None, {"novelty_pressure": 0.8}, {"selection_bias": 0.5})
            artifact_id = register_evaluation(evaluation, {"novelty_pressure": 0.8}, 0.73, parent="root")
            rows = load_all()
            assert len(rows) == 1
            assert rows[0]["id"] == artifact_id
            assert rows[0]["evaluation"]["score"] > 0.0
        finally:
            os.environ.pop("METAOS_EVALUATION_REGISTRY", None)
