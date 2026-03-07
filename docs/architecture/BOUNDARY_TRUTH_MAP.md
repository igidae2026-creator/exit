# Boundary Truth Map

This matrix declares canonical ownership, compatibility-only surfaces, and forbidden imports.

| Layer | Canonical owner | Responsibilities | Compatibility-only surfaces | Forbidden imports |
|---|---|---|---|---|
| Constitutional kernel | `genesis/` | append-only truth law, replay restore protocol, minimal invariant law | `core/`, `kernel/`, `metaos/kernel/` | domain adapters, observer projections |
| Runtime loop | `runtime/` | pressure->allocation->questing orchestration, failure protocol, state machine | `loop/`, `metaos/runtime/` | domain-specific business logic |
| Artifact | `artifact/` | immutable artifact registration, lineage and archive semantics | `metaos/registry/` shims | direct CLI/op mutation |
| Domains | `domains/` | contracts, loader, genome mutation/recombination/crossbreed | `metaos/domains/` | genesis replay primitives |
| Validation | `validation/` | boundary checks, invariant checks, gate enforcement | n/a | runtime state mutation |
| A/B/C ecology | `metaos_a/` `metaos_b/` `metaos_c/` | single-unit exploration, multi-unit allocation, civilization topology/memory | `metaos/` transitional wrappers | bypassing runtime pressure/allocation contracts |
| Operator surfaces | `app/`, `metaos/cli.py`, `ops/` | command routing, health/status/replay/validation entrypoints | none | domain/runtime business logic |

## Compatibility classification
- **Canonical:** `genesis/`, `runtime/`, `artifact/`, `domains/`, `validation/`, `metaos_a/`, `metaos_b/`, `metaos_c/`, `app/`, `observer/`, `ops/`.
- **Compatibility:** `core/`, `kernel/`, `evolution/`, `loop/`, `metaos/kernel/`, `metaos/runtime/`, `metaos/domains/`.
- **Deprecated redirect targets:** compatibility surfaces should import canonical modules and avoid duplicated logic.
- **Retirement rule:** a compatibility surface can be retired only after all imports are redirected and CI boundary checks remain green.
