# METAOS Documentation Index

Canonical owners:
- `genesis/` truth spine and replay invariants.
- `runtime/` stage-based orchestration and policy/runtime evolution.
- `artifact/` immutable artifact registry, archive, lineage graph.
- `domains/` domain lifecycle, contracts, and expansion.
- `validation/` GENESIS law, boundary and constitution checks.
- `metaos_a/`, `metaos_b/`, `metaos_c/` civilization decomposition layers.

Compatibility-only shims:
- `core/`, `kernel/`, `evolution/`
- `metaos/kernel/`, `metaos/runtime/`, `metaos/domains/`

Migration/shim rules:
1. New runtime logic MUST land in canonical owners.
2. Deprecated surfaces MAY only re-export canonical APIs.
3. Shim tests enforce compatibility contracts.

Primary references:
- [GENESIS](./core/GENESIS.md)
- [METAOS Final Definition](./core/METAOS_FINAL_DEFINITION.md)
- [Architecture Layers](./architecture/LAYERS.md)
- [Architecture Boundaries](./architecture/BOUNDARIES.md)
