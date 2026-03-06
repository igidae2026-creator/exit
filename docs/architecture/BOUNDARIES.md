# Boundaries

GENESIS defines the boundary model.

Allowed responsibilities:
- `genesis`: append-only truth, replay, invariants, supervisor recovery
- `metaos_a`: domain exploration execution per domain
- `metaos_b`: exploration scheduling, experiment selection, cross-domain allocation
- `metaos_c`: civilization memory, discovery, topology, long-horizon strategy generation
- `runtime`: orchestration, pressure, economy, civilization dynamics, resource allocation
- `artifact`: append-only artifact storage, registry, lineage, archive
- `domains`: domain contracts, domain runtimes, genomes, resources
- `validation`: laws, contracts, system gates

Forbidden crossings:
- `genesis` must not contain domain logic
- `kernel` must not contain domain logic
- `runtime` must not define artifact storage primitives
- `domains` must not redefine replay or truth spine logic
- `validation` must not mutate runtime state

Deprecated compatibility files:
- `core/*`
- `kernel/*`
- `metaos/kernel/*`
- `metaos/runtime/*`
- `evolution/*`

These remain transitional compatibility only. GENESIS is the canonical execution kernel, and METAOS-A/B/C remain the canonical higher layers.
