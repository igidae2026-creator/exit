from ecosystem.knowledge_network import knowledge_network_state


def test_knowledge_network_tracks_sources_links_and_flow() -> None:
    out = knowledge_network_state(
        [
            {"node_id": "n1", "knowledge_links": ["n2", "n3"]},
            {"node_id": "n2", "knowledge_links": ["n1"]},
        ]
    )["knowledge_graph"]
    assert out["knowledge_sources"] == ["n1", "n2"]
    assert out["knowledge_flow"] == 3
    assert out["knowledge_links"]["n1->n2"] == 1
