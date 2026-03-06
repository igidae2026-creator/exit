# Boundaries

GENESIS defines the boundary model.

Allowed responsibilities:
- `kernel`: truth logs, replay, invariants, supervisor recovery
- `runtime`: orchestration, pressure, economy, civilization dynamics, resource allocation
- `artifact`: append-only artifact storage, registry, lineage, archive
- `domains`: domain contracts, domain runtimes, genomes, resources
- `validation`: laws, contracts, system gates

Forbidden crossings:
- `kernel` must not contain domain logic
- `runtime` must not define artifact storage primitives
- `domains` must not redefine replay or truth spine logic
- `validation` must not mutate runtime state

Deprecated compatibility files:
- `core/replay.py`
- `core/supervisor.py`
- `evolution/pressure_engine.py`
- `evolution/quota_allocator.py`
- `evolution/quest_ecology.py`
- `evolution/quest_generator.py`

These remain as shims until callers are fully converged onto canonical package names.
