from pathlib import Path


RUNTIME_REAL_OWNERS = (
    "runtime/oed_orchestrator.py",
    "runtime/soak_runner.py",
    "runtime/exploration_cycle.py",
    "runtime/exploration_economy.py",
    "runtime/exploration_loop.py",
    "runtime/knowledge_system.py",
    "runtime/lineage_ecology.py",
    "runtime/policy_runtime.py",
    "runtime/pressure_model.py",
    "runtime/resource_allocator.py",
    "runtime/allocator_artifact.py",
    "runtime/artifact_civilization.py",
    "runtime/artifact_population.py",
    "runtime/civilization_governor.py",
    "runtime/civilization_selection.py",
    "runtime/civilization_stability.py",
    "runtime/collapse_guard.py",
    "runtime/domain_creation.py",
    "runtime/domain_pool.py",
    "runtime/domain_router.py",
    "runtime/evaluation_ecology.py",
    "runtime/evolve_exploration_strategy.py",
    "runtime/exploration_market_stability.py",
    "runtime/exploration_strategy_artifact.py",
    "runtime/exploration_topology.py",
    "runtime/hysteresis.py",
    "runtime/memory_pressure.py",
    "runtime/meta_cooldown.py",
    "runtime/meta_exploration.py",
    "runtime/meta_quest_engine.py",
    "runtime/kernel_adapter.py",
    "runtime/metrics_runtime.py",
    "runtime/policy_store.py",
    "runtime/pressure_ecology.py",
    "runtime/pressure_engine.py",
    "runtime/pressure_market.py",
    "runtime/quest_ecology.py",
    "runtime/quest_generator.py",
    "runtime/quest_state.py",
    "runtime/quota_allocator.py",
    "runtime/quota_policy.py",
    "runtime/quest_system.py",
    "runtime/recovery_allocator.py",
    "runtime/replay_state.py",
    "runtime/repair_system.py",
    "runtime/strategy_of_strategy.py",
    "runtime/strategy_genome.py",
    "runtime/supervisor.py",
)


def test_runtime_real_owner_files_are_not_metaos_runtime_wrappers() -> None:
    forbidden = (
        "from metaos.runtime.",
        "import metaos.runtime.",
        "from core.",
        "import core.",
        "from evolution.",
        "import evolution.",
        "sys.modules[__name__] = _canonical",
    )
    for relpath in RUNTIME_REAL_OWNERS:
        text = Path(relpath).read_text(encoding="utf-8")
        assert not any(token in text for token in forbidden), relpath
