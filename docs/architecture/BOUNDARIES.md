# Boundaries

GENESIS defines the boundary model.

Ownership truth:
- `runtime/` owns `civilization_state`, pressure, allocation, and orchestration stages
- `domains/` owns domain logic and domain evolution helpers
- `artifact/` owns immutable artifact storage, registry, lineage, and archive
- `validation/` owns invariant and boundary enforcement
- `genesis/` owns append-only truth, replay, and kernel recovery law

Forbidden crossings:
- `genesis/` must not absorb domain logic
- `runtime/` must not redefine artifact storage primitives
- `domains/` must not redefine replay or truth logic
- `validation/` must not mutate runtime state
- `app/` and `observer/` must not contain business logic

Compatibility-only surfaces:
- `core/*`
- `kernel/*`
- `evolution/*`
- `metaos/kernel/*`
- `metaos/runtime/*`
- `metaos/domains/*`
