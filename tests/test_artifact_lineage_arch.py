from artifact.lineage import build_lineage_view, lineage_chain


def test_artifact_lineage_builds_multi_parent_view() -> None:
    rows = [
        {"artifact_id": "a", "refs": {"parents": []}},
        {"artifact_id": "b", "refs": {"parents": ["a"]}},
        {"artifact_id": "c", "refs": {"parents": ["a", "b"]}},
    ]
    graph = build_lineage_view(rows)
    assert graph["a"] == ["b", "c"]
    assert lineage_chain("c", rows) == ["c", "a"]

