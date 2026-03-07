import os
import tempfile
from pathlib import Path

from artifact.registry import load_envelope, register_envelope
from validation.artifact_law import validate_artifact_law


def test_artifact_law_requires_immutable_required_fields() -> None:
    out = validate_artifact_law(
        {
            "artifact_id": "x",
            "artifact_type": "policy",
            "lineage_id": "x",
            "parent_ids": [],
            "domain": "policy",
            "policy_id": "policy:x",
            "strategy_id": "",
            "payload": {},
            "evaluation_vector": {},
            "fitness_vector": {"quality": 0.0},
            "creation_timestamp": 1.0,
            "runtime_context": {},
            "provenance": {},
            "replay_checksum": "abc",
            "content_hash": "def",
            "immutable": True,
        }
    )
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
            assert envelope["content_hash"]
            assert envelope["replay_checksum"]
            assert "evaluation_vector" in envelope
            assert validate_artifact_law(envelope)["ok"] is True
        finally:
            os.environ.pop("METAOS_REGISTRY", None)
            os.environ.pop("METAOS_ARTIFACT_STORE", None)
