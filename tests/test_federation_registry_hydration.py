import os
import tempfile

from artifact.civilization_registry import civilization_state
from federation.federation_hydration import hydrate_artifact


def test_registry_accounts_for_mirrored_artifacts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            hydrate_artifact("artifact_origin", origin_node="node_a")
            state = civilization_state()
            assert state["mirrored_external_artifacts"] == 1
            assert state["hydration_rate"] > 0.0
            assert state["mirror_lineage_count"] == 1
        finally:
            os.environ.pop("METAOS_ROOT", None)
