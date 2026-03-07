import os
import tempfile

from ecosystem.ecosystem_registry import ecosystem_registry_state, register_node


def test_ecosystem_registry_tracks_registered_and_active_nodes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            register_node({"node_id": "n1", "active": True})
            register_node({"node_id": "n2", "active": False})
            state = ecosystem_registry_state()
            assert state["registered_nodes"] == ["n1", "n2"]
            assert state["active_nodes"] == ["n1"]
        finally:
            os.environ.pop("METAOS_ROOT", None)
