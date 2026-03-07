from pathlib import Path


SHIM_HEADER = "Deprecated compatibility shim. Canonical owner:"
ALLOWED_PREFIXES = ('"""', "Deprecated ", "Canonical ", "from ", "import ", "sys.modules", "__all__")


def _has_shim_header(text: str) -> bool:
    return "Deprecated compatibility shim." in text and "Canonical owner:" in text


def test_deprecated_surfaces_are_small() -> None:
    for root_name in ("core", "kernel", "evolution", "metaos/kernel", "metaos/runtime", "metaos/domains"):
        root = Path(root_name)
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if path.name == "__init__.py":
                continue
            text = path.read_text(encoding="utf-8").strip()
            assert len(text.splitlines()) <= 10, str(path)
            assert _has_shim_header(text), str(path)
            for line in text.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                assert stripped.startswith(ALLOWED_PREFIXES), f"{path}: {line}"


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
        Path("metaos/runtime/soak_runner.py"),
        Path("metaos/domains/domain_crossbreed.py"),
        Path("metaos/domains/domain_genome_mutation.py"),
        Path("metaos/domains/domain_recombination.py"),
        Path("core/artifact.py"),
        Path("core/constitution_guard.py"),
        Path("core/event_log.py"),
        Path("core/kernel_adapter.py"),
        Path("core/log.py"),
        Path("core/loop.py"),
        Path("core/metrics.py"),
        Path("core/policy.py"),
        Path("core/quest.py"),
        Path("core/registry.py"),
        Path("core/replay.py"),
        Path("core/strategy_genome.py"),
        Path("core/supervisor.py"),
        Path("kernel/contracts.py"),
        Path("kernel/policy_runtime.py"),
        Path("kernel/recovery.py"),
        Path("evolution/evolve.py"),
        Path("evolution/pressure_engine.py"),
        Path("evolution/quest_ecology.py"),
        Path("evolution/quest_generator.py"),
        Path("evolution/quota_allocator.py"),
        Path("metaos/kernel/__init__.py"),
        Path("metaos/kernel/replay.py"),
    ]
    for path in shim_paths:
        text = path.read_text(encoding="utf-8")
        assert _has_shim_header(text), str(path)
