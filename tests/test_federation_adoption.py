import os
import tempfile

from federation.federation_adoption import materialize_artifact
from federation.federation_state import federation_state


def test_federation_adoption_materializes_external_artifacts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        os.environ["METAOS_FEDERATION_ENABLED"] = "1"
        try:
            materialize_artifact("artifact_ext", "observed", {"origin_node": "node_a"})
            materialize_artifact("artifact_ext", "imported", {"origin_node": "node_a"})
            materialize_artifact("artifact_ext", "adopted", {"origin_node": "node_a"})
            materialize_artifact("artifact_ext", "activated", {"origin_node": "node_a"})
            state = federation_state()
            assert state["observed_external_artifacts"] == 1
            assert state["imported_external_artifacts"] == 1
            assert state["adopted_external_artifacts"] == 1
            assert state["active_external_artifacts"] == 1
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_FEDERATION_ENABLED", None)
