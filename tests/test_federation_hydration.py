import os
import tempfile

from artifact.registry import rows
from federation.federation_hydration import hydrate_artifact


def test_hydrated_artifact_appears_in_local_registry() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            result = hydrate_artifact("artifact_origin", origin_node="node_a", payload={"value": 1})
            assert result["hydrated"] is True
            mirrored = [row for row in rows() if str(row.get("artifact_scope", "")) == "mirrored"]
            assert len(mirrored) == 1
            assert mirrored[0]["origin_artifact_id"] == "artifact_origin"
            assert mirrored[0]["origin_node"] == "node_a"
        finally:
            os.environ.pop("METAOS_ROOT", None)
