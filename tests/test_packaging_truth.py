from pathlib import Path

from validation.ownership_manifest import packaged_roots


def test_pyproject_matches_top_level_package_layout() -> None:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'package-dir = {"" = "src"}' not in text
    assert 'where = ["."]' in text
    assert "requires = []" in text
    assert 'build-backend = "build_backend"' in text
    assert 'backend-path = ["."]' in text
    for package_name in packaged_roots():
        assert f'"{package_name}*"' in text or f'"{package_name}"' in text


def test_setup_py_has_no_fake_src_or_stale_package_hints() -> None:
    text = Path("setup.py").read_text(encoding="utf-8")
    assert "src*" not in text
    assert 'where="."' in text
    assert "insights*" not in text
    assert "metrics*" not in text
    for package_name in packaged_roots():
        assert f'"{package_name}*"' in text or f'"{package_name}"' in text


def test_packaging_truth_matches_actual_tree() -> None:
    roots = {path.name for path in Path(".").iterdir() if path.is_dir()}
    for package_name in packaged_roots():
        assert package_name in roots


def test_repository_local_build_backend_exists() -> None:
    assert Path("build_backend.py").exists()
