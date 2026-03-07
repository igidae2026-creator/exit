from ecosystem.domain_clusters import domain_cluster_state


def test_domain_clusters_group_domains_and_activity() -> None:
    out = domain_cluster_state(
        [
            {"node_domains": ["bio_alpha", "bio_beta"], "cluster": "bio"},
            {"node_domains": ["astro_alpha"], "cluster": "astro"},
        ]
    )
    assert sorted(out["domain_clusters"]) == ["astro", "bio"]
    assert out["cluster_activity"]["bio"] == 2
    assert out["cluster_lineage_density"]["astro"] > 0.0
