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
