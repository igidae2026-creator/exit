from pathlib import Path


def test_platform_layer_framing_doc_exists_and_names_higher_constraints() -> None:
    path = Path("docs/runtime/PLATFORM_LAYER_FRAMING.md")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    for token in (
        "exploration OS",
        "lineage",
        "replayability",
        "append-only truth",
        "platform layer should bend",
    ):
        assert token in text


def test_runtime_status_docs_reference_platform_layer_framing() -> None:
    for rel in (
        "docs/runtime/ADAPTER_RUNTIME_CORE.md",
        "docs/runtime/CURRENT_PLATFORM_STATUS.md",
        "docs/runtime/NEXT_OPERATING_PRIORITY.md",
    ):
        text = Path(rel).read_text(encoding="utf-8")
        assert "PLATFORM_LAYER_FRAMING.md" in text
