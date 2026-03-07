from pathlib import Path


def test_product_tree_ignores_runtime_noise() -> None:
    text = Path(".gitignore").read_text(encoding="utf-8")
    assert "__pycache__/" in text
    assert "snapshots/" in text
    assert "*.bak" in text
    assert ".metaos_runtime/" in text


def test_product_tree_has_no_fake_src_packaging_claim() -> None:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'package-dir = {"" = "src"}' not in text
