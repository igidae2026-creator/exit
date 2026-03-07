import os
import tempfile

from ecosystem.ecosystem_registry import ecosystem_registry_state
from ecosystem.node_discovery import discover_nodes


def test_node_discovery_registers_capabilities_and_specializations() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            discover_nodes(
                [
                    {
                        "node_id": "node_1",
                        "node_domains": ["d1", "d2"],
                        "node_capacity": 6,
                        "node_artifact_rate": 1.2,
                        "node_specializations": ["novelty"],
                    }
                ]
            )
            state = ecosystem_registry_state()
            assert state["registered_nodes"] == ["node_1"]
            assert state["rows"][0]["node_specializations"] == ["novelty"]
        finally:
            os.environ.pop("METAOS_ROOT", None)
