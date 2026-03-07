import os
import tempfile

from federation.federation_state import federation_state
from metaos_c.domain_discovery import discover_domains


def test_domain_propagation_tracks_origin_depth_and_adoption() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        os.environ["METAOS_FEDERATION_ENABLED"] = "1"
        os.environ["METAOS_NODE_ID"] = "node_a"
        try:
            domains = discover_domains(
                {"knowledge_density": 0.8, "domain_distribution": {}},
                {"novelty_pressure": 0.8, "diversity_pressure": 0.7, "domain_shift_pressure": 0.6},
                {"domain_expansion_budget": 1},
            )
            state = federation_state()
            assert domains
            assert state["shared_domains"]
            assert state["domain_propagation_rate"] > 0.0
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_FEDERATION_ENABLED", None)
            os.environ.pop("METAOS_NODE_ID", None)
