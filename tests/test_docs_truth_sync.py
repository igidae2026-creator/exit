from pathlib import Path


DOCS = [
    "GENESIS.md",
    "README.md",
    "RUNBOOK.md",
    "docs/core/GENESIS.md",
    "docs/core/METAOS_FINAL_DEFINITION.md",
    "docs/architecture/LAYERS.md",
    "docs/architecture/BOUNDARIES.md",
    "docs/architecture/WHY_METAOS.md",
    "docs/ops/OPERATIONS.md",
    "docs/ops/OPERATIONAL_AUTONOMY_STATUS.md",
    "docs/ops/RECOVERY.md",
    "docs/ops/RELEASE.md",
]


def test_docs_sync_mentions_canonical_loop_and_derived_state() -> None:
    combined = "\n".join(Path(path).read_text(encoding="utf-8") for path in DOCS)
    assert "signal -> generate -> evaluate -> select -> mutate -> archive -> repeat" in combined
    assert "civilization_state" in combined
    assert "derived operational state" in combined or "replay-derived" in combined
    assert "GENESIS -> METAOS-A -> METAOS-B -> METAOS-C" in combined


def test_runtime_threshold_truth_chains_into_ops_and_release_docs() -> None:
    runtime_status = Path("docs/runtime/CURRENT_PLATFORM_STATUS.md").read_text(encoding="utf-8")
    runtime_snapshot = Path("docs/runtime/THRESHOLD_OPERATING_SNAPSHOT.md").read_text(encoding="utf-8")
    ops_status = Path("docs/ops/OPERATIONAL_AUTONOMY_STATUS.md").read_text(encoding="utf-8")
    ops_doc = Path("docs/ops/OPERATIONS.md").read_text(encoding="utf-8")
    release_doc = Path("docs/ops/RELEASE.md").read_text(encoding="utf-8")
    assert "THRESHOLD_OPERATING_SNAPSHOT.md" in runtime_status
    assert "/tmp/metaos_threshold_autonomy_clean/latest_status.json" in runtime_snapshot
    assert "docs/runtime/THRESHOLD_OPERATING_SNAPSHOT.md" in ops_status
    assert "OPERATIONAL_AUTONOMY_STATUS.md" in ops_doc
    assert "OPERATIONAL_AUTONOMY_STATUS.md" in release_doc
