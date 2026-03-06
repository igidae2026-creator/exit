# METAOS

METAOS is not a problem-solving app. METAOS is a bounded autonomous exploration civilization engine.

GENESIS is the top-level system law:
- [GENESIS](/home/meta_os/metaos/docs/core/GENESIS.md)
- [METAOS Final Definition](/home/meta_os/metaos/docs/core/METAOS_FINAL_DEFINITION.md)
- [METAOS Constitution](/home/meta_os/metaos/docs/00_METAOS_CONSTITUTION.md)
- [METAOS Master Specification](/home/meta_os/metaos/docs/01_METAOS_MASTER_SPEC.md)
- [Architecture Layers](/home/meta_os/metaos/docs/architecture/LAYERS.md)
- [Architecture Boundaries](/home/meta_os/metaos/docs/architecture/BOUNDARIES.md)
- [Why METAOS](/home/meta_os/metaos/docs/architecture/WHY_METAOS.md)

Hierarchy:
- `GENESIS`: canonical execution kernel
- `METAOS-A`: domain exploration unit
- `METAOS-B`: exploration manager
- `METAOS-C`: civilization engine

Canonical package owners:
- `genesis/`
- `metaos_a/`
- `metaos_b/`
- `metaos_c/`
- `artifact/`
- `domains/`
- `validation/`
- `runtime/`
- `app/`

Deprecated compatibility surfaces remain transitional only:
- `core/`
- `kernel/`
- `evolution/`
- `metaos/kernel/`
- `metaos/runtime/`

## Why Use METAOS

Use METAOS when you need a long-running exploration system that continuously signals, generates, evaluates, selects, mutates, archives, and replays evolving artifacts under invariant constraints.

## Who Should Use METAOS

- teams building bounded autonomy
- engineers who need replayable state and append-only truth
- operators who want pressure-driven exploration and runtime policy evolution

## When Not To Use METAOS

- when you want a single-shot assistant
- when you want a direct problem-solving app
- when replay, lineage, and invariant enforcement are unnecessary

## What METAOS Uniquely Enables

- continuous bounded exploration instead of one-shot execution
- artifact lineage and replayable civilization memory
- runtime policy evolution without restart
- domain autonomy behind a minimal kernel and explicit validation laws

## Operational Maturity

- philosophically complete
- operationally durable
- release-shaped
- replay-safe
- long-run ready

## Local Validation

```bash
. .venv/bin/activate
export PYTHONPATH="$PWD"
pytest -q
```
