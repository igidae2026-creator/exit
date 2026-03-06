import os
import tempfile
from pathlib import Path

from artifact.registry import load_envelope, register_envelope
from validation.artifact_law import validate_artifact_law


def test_artifact_law_requires_immutable_required_fields() -> None:
    out = validate_artifact_law({"artifact_id": "x", "artifact_type": "policy", "parent_ids": [], "payload": {}, "score_vector": {}, "created_at": 1.0, "immutable": True})
    assert out["ok"] is True


def test_artifact_writes_obey_artifact_law() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_REGISTRY"] = str(Path(tmp) / "artifact_registry.jsonl")
        os.environ["METAOS_ARTIFACT_STORE"] = str(Path(tmp) / "artifact_store")
        try:
            artifact_id = register_envelope(aclass="policy", atype="runtime_policy", spec={"policy": {"mutation_rate": 0.2}})
            envelope = load_envelope(artifact_id)
            assert envelope is not None
            assert envelope["immutable"] is True
            assert validate_artifact_law(envelope)["ok"] is True
        finally:
            os.environ.pop("METAOS_REGISTRY", None)
            os.environ.pop("METAOS_ARTIFACT_STORE", None)
