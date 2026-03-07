from federation.federation_topology import topology_state


def test_federation_topology_reports_degree_and_flow() -> None:
    out = topology_state(["n1", "n2", "n3", "n4"], "ring", artifact_events=8, knowledge_events=4)
    assert out["topology_type"] == "ring"
    assert out["node_degree"]["n1"] == 2
    assert out["artifact_flow_rate"] > 0.0
    assert out["knowledge_flow_rate"] > 0.0
