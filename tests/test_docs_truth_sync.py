from pathlib import Path


DOCS = [
    "README.md",
    "RUNBOOK.md",
    "docs/core/GENESIS.md",
    "docs/core/METAOS_FINAL_DEFINITION.md",
    "docs/architecture/LAYERS.md",
    "docs/architecture/BOUNDARIES.md",
    "docs/architecture/WHY_METAOS.md",
    "docs/ops/OPERATIONS.md",
    "docs/ops/RECOVERY.md",
    "docs/ops/RELEASE.md",
]


def test_docs_sync_mentions_civilization_state_and_flow() -> None:
    combined = "\n".join(Path(path).read_text(encoding="utf-8") for path in DOCS)
    assert "civilization_state" in combined
    assert "-> pressure" in combined
    assert "-> allocation" in combined
    assert "-> questing" in combined
    assert "-> artifact evolution" in combined
    assert "-> domain evolution" in combined
    assert "-> memory accumulation" in combined
    assert "GENESIS -> METAOS-A -> METAOS-B -> METAOS-C" in combined

