from pathlib import Path


def test_kernel_contains_no_domain_logic_imports() -> None:
    kernel_root = Path("kernel")
    forbidden = ("from domains", "import domains", "from metaos.domains", "import metaos.domains")
    for path in kernel_root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not any(token in text for token in forbidden), str(path)


def test_append_only_truth_files_remain_canonical() -> None:
    text = Path("kernel/spine.py").read_text(encoding="utf-8")
    assert "events.jsonl" in text
    assert "metrics.jsonl" in text
    assert "artifact_registry.jsonl" in text
