import os
import tempfile
from pathlib import Path

from artifact.registry import load_envelope, register_envelope, rows


def test_registry_rows_rebuild_full_envelope_from_store() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_REGISTRY"] = str(Path(tmp) / "artifact_registry.jsonl")
        os.environ["METAOS_ARTIFACT_STORE"] = str(Path(tmp) / "artifact_store")
        try:
            artifact_id = register_envelope(aclass="domain", atype="code_domain", spec={"name": "code_domain"})
            compact_rows = rows()
            assert "body_ref" in compact_rows[0]
            assert "spec" not in compact_rows[0]
            envelope = load_envelope(artifact_id)
            assert envelope is not None
            assert envelope["spec"]["name"] == "code_domain"
        finally:
            os.environ.pop("METAOS_REGISTRY", None)
            os.environ.pop("METAOS_ARTIFACT_STORE", None)

