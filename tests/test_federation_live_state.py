import os
import tempfile

from federation.federation_adoption import materialize_artifact, materialize_domain, materialize_evaluation, materialize_policy
from runtime.civilization_state import civilization_state


def test_federation_live_state_reflects_materialized_external_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        os.environ["METAOS_FEDERATION_ENABLED"] = "1"
        try:
            materialize_artifact("artifact_live", "activated", {"origin_node": "node_x"})
            materialize_domain("domain_live", "activated", {"origin_node": "node_x"})
            materialize_policy("policy_live", "activated", {"origin_node": "node_x"})
            materialize_evaluation("evaluation_live", "activated", {"origin_node": "node_x"})
            state = civilization_state(history=[])
            assert state["active_external_artifacts"] == 1
            assert state["active_imported_domains"] == 1
            assert state["active_external_policies"] == 1
            assert state["active_external_evaluation_generations"] == 1
            assert state["federation_activation_rate"] > 0.0
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_FEDERATION_ENABLED", None)
