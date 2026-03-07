import os
import tempfile

from federation.federation_exchange import diffuse_policy, exchange_knowledge, export_artifact, propagate_domain
from runtime.observability import federation_summary, node_summary


def test_federation_observability_exposes_rates_and_topology() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        os.environ["METAOS_FEDERATION_ENABLED"] = "1"
        os.environ["METAOS_FEDERATION_TOPOLOGY"] = "ring"
        try:
            export_artifact("a1", {"payload": "x"})
            propagate_domain("d1")
            diffuse_policy("p1", {"mode": "safe"})
            exchange_knowledge({"summary": 1})
            summary = federation_summary()
            node = node_summary()
            assert summary["artifact_exchange_rate"] > 0.0
            assert summary["policy_diffusion_rate"] > 0.0
            assert summary["knowledge_flow_rate"] > 0.0
            assert summary["federation_topology"]["topology_type"] == "ring"
            assert node["node_topology"]["topology_type"] == "ring"
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_FEDERATION_ENABLED", None)
            os.environ.pop("METAOS_FEDERATION_TOPOLOGY", None)
