import os
import tempfile

from federation.federation_exchange import exchange_knowledge
from runtime.civilization_memory import civilization_state


def test_knowledge_propagation_is_measurable_and_append_only() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        os.environ["METAOS_FEDERATION_ENABLED"] = "1"
        try:
            exchange_knowledge({"knowledge_density": 0.7}, source_node="node_a")
            exchange_knowledge({"knowledge_density": 0.8}, source_node="node_b")
            state = civilization_state()
            assert state["knowledge_exchange_events"] == 2
            assert state["federation_memory_growth"] > 0.0
            assert state["knowledge_import_count"] == 2
            assert state["knowledge_export_count"] == 2
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_FEDERATION_ENABLED", None)
