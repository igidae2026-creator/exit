import os
import tempfile

from federation.federation_hydration import hydrate_artifact
from federation.federation_state import federation_state


def test_foreign_origin_distribution_is_tracked() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            hydrate_artifact("artifact_a", origin_node="node_a")
            hydrate_artifact("artifact_b", origin_node="node_b")
            state = federation_state()
            assert state["foreign_origin_distribution"]["node_a"] == 1
            assert state["foreign_origin_distribution"]["node_b"] == 1
        finally:
            os.environ.pop("METAOS_ROOT", None)
