from pathlib import Path

from validation.ownership_manifest import load_ownership_manifest, ownership_rows, packaged_roots, release_paths


def test_ownership_manifest_covers_required_top_level_surfaces() -> None:
    manifest = load_ownership_manifest()
    assert manifest["version"] >= 1
    paths = {row["path"] for row in ownership_rows()}
    for required in (
        "app",
        "artifact",
        "core",
        "docs",
        "domains",
        "ecosystem",
        "evolution",
        "federation",
        "genesis",
        "kernel",
        "loop",
        "metaos",
        "metaos-build-prompts",
        "metaos_a",
        "metaos_b",
        "metaos_c",
        "observer",
        "ops",
        "runtime",
        "scripts",
        "signal",
        "strategy",
        "tests",
        "validation",
    ):
        assert required in paths


def test_ownership_manifest_paths_exist() -> None:
    for path in release_paths() + packaged_roots():
        assert Path(path).exists(), path


def test_ownership_manifest_has_no_limbo_classifications() -> None:
    for row in ownership_rows():
        assert row["classification"] in {
            "canonical",
            "compatibility_shim",
            "runtime_helper",
            "release_only",
            "repo_only",
            "canonical_docs",
            "canonical_metadata",
        }
        assert row["rationale"]
