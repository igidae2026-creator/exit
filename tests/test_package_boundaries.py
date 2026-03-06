from pathlib import Path


def test_kernel_contains_no_domain_logic_imports() -> None:
    kernel_root = Path("kernel")
    forbidden = ("from domains", "import domains", "from metaos.domains", "import metaos.domains")
    for path in kernel_root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not any(token in text for token in forbidden), str(path)


def test_genesis_contains_no_domain_logic_imports() -> None:
    genesis_root = Path("genesis")
    forbidden = ("from domains", "import domains", "from metaos.domains", "import metaos.domains")
    for path in genesis_root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not any(token in text for token in forbidden), str(path)


def test_append_only_truth_files_remain_canonical() -> None:
    text = Path("genesis/spine.py").read_text(encoding="utf-8")
    assert "events.jsonl" in text
    assert "metrics.jsonl" in text
    assert "artifact_registry.jsonl" in text


def test_runtime_avoids_deprecated_runtime_imports_when_canonical_exists() -> None:
    forbidden = (
        "from metaos.runtime.oed_orchestrator",
        "from metaos.runtime.policy_runtime",
        "from metaos.runtime.exploration_economy",
        "from metaos.runtime.exploration_cycle",
        "from metaos.runtime.exploration_loop",
        "from metaos.runtime.knowledge_system",
        "from metaos.runtime.lineage_ecology",
        "from metaos.runtime.pressure_model",
        "from metaos.runtime.resource_allocator",
    )
    for path in Path("runtime").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not any(token in text for token in forbidden), str(path)
