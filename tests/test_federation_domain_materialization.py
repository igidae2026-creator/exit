import os
import tempfile

from federation.federation_adoption import materialize_domain
from runtime.civilization_state import civilization_state


def test_federation_domain_materialization_can_activate_imported_domains() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        os.environ["METAOS_FEDERATION_ENABLED"] = "1"
        try:
            materialize_domain("domain_ext", "imported", {"origin_node": "node_b"})
            materialize_domain("domain_ext", "adopted", {"origin_node": "node_b"})
            materialize_domain("domain_ext", "activated", {"origin_node": "node_b"})
            state = civilization_state(history=[])
            assert state["imported_domains"] == 1
            assert state["adopted_domains"] == 1
            assert state["active_imported_domains"] == 1
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_FEDERATION_ENABLED", None)
