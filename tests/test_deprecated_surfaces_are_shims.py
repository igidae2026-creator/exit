from pathlib import Path


SHIM_HEADER = "Deprecated compatibility shim. Canonical owner:"


def test_deprecated_surfaces_are_small() -> None:
    for root_name in ("kernel", "evolution", "metaos/kernel", "metaos/runtime"):
        root = Path(root_name)
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if path.name == "__init__.py":
                continue
            assert len(path.read_text(encoding="utf-8").splitlines()) <= 220, str(path)


def test_runtime_deprecated_shims_have_canonical_header() -> None:
    shim_paths = [
        Path("metaos/runtime/exploration_cycle.py"),
        Path("metaos/runtime/exploration_economy.py"),
        Path("metaos/runtime/exploration_loop.py"),
        Path("metaos/runtime/knowledge_system.py"),
        Path("metaos/runtime/lineage_ecology.py"),
        Path("metaos/runtime/oed_orchestrator.py"),
        Path("metaos/runtime/policy_runtime.py"),
        Path("metaos/runtime/pressure_model.py"),
        Path("metaos/runtime/resource_allocator.py"),
    ]
    for path in shim_paths:
        text = path.read_text(encoding="utf-8")
        assert text.startswith('"""' + SHIM_HEADER), str(path)
