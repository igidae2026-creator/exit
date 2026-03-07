# Canonical Import Graph

## Purpose

This graph marks the allowed high-level dependency direction for canonical METAOS surfaces.

## Canonical Flow

- `genesis` provides append-only truth, replay, invariants, and recovery primitives.
- `artifact` depends on `genesis` for event and registry truth.
- `domains` depends on `artifact` and `genesis` contracts, not on operator surfaces.
- `runtime` depends on `genesis`, `artifact`, `domains`, `metaos_a`, `metaos_b`, `metaos_c`, `observer`, `ecosystem`, and `federation`.
- `metaos` and `app` provide CLI entrypoints over runtime and observer projections.
- `validation` may depend on canonical owners to verify behavior, but canonical runtime must not depend on docs or ops.

## Forbidden Drift

- `app/` must not own runtime business logic.
- Compatibility shims must not become import roots for new logic.
- Domain onboarding must not require direct edits inside `genesis/`.

## Compatibility Notes

- `core/`, `kernel/`, `evolution/`, and `metaos/runtime/` remain shims and bridges only.
- `civilization` and `run` profile names remain aliases over the production profile for compatibility.
