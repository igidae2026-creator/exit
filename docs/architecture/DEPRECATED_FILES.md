# Deprecated Files

Compatibility shims retained during convergence:
- `core/*` transition surface for older runtime entrypoints
- `kernel/*`
- `metaos/kernel/*`
- `metaos/runtime/*`
- `evolution/*`

Truth rule:
- deprecated files are not canonical owners
- canonical imports should target canonical packages first
- compatibility files remain only to preserve legacy import paths

Shim files retained intentionally:
- `core/artifact.py` -> `artifact.runtime_store`
- `core/constitution_guard.py` -> `validation.immutability`
- `core/event_log.py` -> `genesis.event_log`
- `core/kernel_adapter.py` -> `runtime.kernel_adapter`
- `core/log.py` -> `genesis.logger`
- `core/loop.py` -> `runtime.core_loop`
- `core/metrics.py` -> `runtime.metrics_runtime`
- `core/policy.py` -> `runtime.policy_store`
- `core/quest.py` -> `runtime.quest_state`
- `core/registry.py` -> `artifact.registry_view`
- `core/replay.py` -> `runtime.replay_state`
- `core/strategy_genome.py` -> `runtime.strategy_genome`
- `core/supervisor.py` -> `runtime.supervisor`
- `kernel/contracts.py` -> `genesis.contracts`
- `kernel/policy_runtime.py` -> `genesis.policy_runtime`
- `kernel/recovery.py` -> `genesis.recovery`
- `metaos/kernel/__init__.py` -> `genesis.replay`
- `metaos/kernel/replay.py` -> `genesis.replay`
- `metaos/runtime/exploration_cycle.py` -> `runtime.exploration_cycle`
- `metaos/runtime/exploration_economy.py` -> `runtime.exploration_economy`
- `metaos/runtime/exploration_loop.py` -> `runtime.exploration_loop`
- `metaos/runtime/knowledge_system.py` -> `runtime.knowledge_system`
- `metaos/runtime/lineage_ecology.py` -> `runtime.lineage_ecology`
- `metaos/runtime/oed_orchestrator.py` -> `runtime.oed_orchestrator`
- `metaos/runtime/policy_runtime.py` -> `runtime.policy_runtime`
- `metaos/runtime/pressure_model.py` -> `runtime.pressure_model`
- `metaos/runtime/resource_allocator.py` -> `runtime.resource_allocator`
- `metaos/runtime/soak_runner.py` -> `runtime.soak_runner`
- `metaos/domains/domain_crossbreed.py` -> `domains.domain_crossbreed`
- `metaos/domains/domain_genome_mutation.py` -> `domains.domain_genome_mutation`
- `metaos/domains/domain_recombination.py` -> `domains.domain_recombination`
- `evolution/evolve.py` -> `runtime.evolve`
- `evolution/pressure_engine.py` -> `runtime.pressure_engine`
- `evolution/quest_ecology.py` -> `runtime.quest_ecology`
- `evolution/quest_generator.py` -> `runtime.quest_generator`
- `evolution/quota_allocator.py` -> `runtime.quota_policy`

Removed deprecated files:
- `core/autonomous_daemon.py`
- `core/guardrail.py`
- `core/llm_provider.py`
- `core/metaos_engine.py`
- `core/mutation.py`
- `core/open_ended_engine.py`
- `core/persistent_swarm.py`
- `core/replay_engine.py`
- `core/shared_replay.py`
- `core/swarm_engine.py`
- `core/swarm_policy.py`

Convergence truth:
- deprecated surfaces are shim-only or removed
- canonical ownership is now carried by `genesis/`, `runtime/`, `artifact/`, `domains/`, and `validation/`
