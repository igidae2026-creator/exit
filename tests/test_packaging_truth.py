from pathlib import Path


def test_pyproject_matches_top_level_package_layout() -> None:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'package-dir = {"" = "src"}' not in text
    assert 'where = ["."]' in text
    for package_name in (
        "app",
        "artifact",
        "domains",
        "genesis",
        "metaos",
        "metaos_a",
        "metaos_b",
        "metaos_c",
        "runtime",
        "validation",
    ):
        assert f'"{package_name}"' in text or f'"{package_name}*"' in text


def test_setup_py_has_no_fake_src_or_stale_package_hints() -> None:
    text = Path("setup.py").read_text(encoding="utf-8")
    assert "src*" not in text
    assert 'where="."' in text
    assert "insights*" not in text
    assert "metrics*" not in text
    assert '"kernel"' not in text
    assert '"evolution"' not in text


def test_packaging_truth_matches_actual_tree() -> None:
    roots = {path.name for path in Path(".").iterdir() if path.is_dir()}
    for package_name in ("app", "artifact", "domains", "genesis", "metaos", "metaos_a", "metaos_b", "metaos_c", "runtime", "validation"):
        assert package_name in roots
