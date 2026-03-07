from pathlib import Path


def test_boundary_truth_map_exists_and_covers_compatibility_surfaces() -> None:
    text = Path("docs/architecture/BOUNDARY_TRUTH_MAP.md").read_text(encoding="utf-8")
    assert "Compatibility classification" in text
    assert "core/" in text
    assert "metaos/runtime/" in text


def test_invariant_traceability_matrix_links_invariants_to_validation_and_ops() -> None:
    text = Path("docs/architecture/INVARIANT_TRACEABILITY.md").read_text(encoding="utf-8")
    assert "Invariant Traceability Matrix" in text
    assert "validation/genesis_invariants.py" in text
    assert "metaos validate" in text
