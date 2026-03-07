import os
import tempfile

from federation.federation_adoption import materialize_policy
from runtime.civilization_state import civilization_state


def test_federation_policy_adoption_remains_bounded() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        os.environ["METAOS_FEDERATION_ENABLED"] = "1"
        try:
            materialize_policy("policy_ext", "observed", {"origin_node": "node_c"})
            materialize_policy("policy_ext", "adopted", {"origin_node": "node_c"})
            materialize_policy("policy_ext", "activated", {"origin_node": "node_c"})
            state = civilization_state(history=[])
            assert state["observed_external_policies"] == 1
            assert state["adopted_external_policies"] == 1
            assert state["active_external_policies"] == 1
            assert 0.0 <= state["federation_influence_score"] <= 1.0
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_FEDERATION_ENABLED", None)
