# Layers

GENESIS is the top-level law. This file describes how the current codebase maps to it.

Hierarchy:
- Human
- METAOS-C
- METAOS-B
- METAOS-A
- GENESIS

Canonical layers:
- `genesis`: [genesis/](/home/meta_os/metaos/genesis)
- `metaos_a`: [metaos_a/](/home/meta_os/metaos/metaos_a)
- `metaos_b`: [metaos_b/](/home/meta_os/metaos/metaos_b)
- `metaos_c`: [metaos_c/](/home/meta_os/metaos/metaos_c)
- `runtime`: [runtime/](/home/meta_os/metaos/runtime)
- `artifact`: [artifact/](/home/meta_os/metaos/artifact)
- `domains`: [domains/](/home/meta_os/metaos/domains)
- `validation`: [validation/](/home/meta_os/metaos/validation)
- `app`: [app/](/home/meta_os/metaos/app)

Legacy compatibility surfaces:
- `kernel/`: GENESIS compatibility shims only
- `metaos/kernel/`: GENESIS compatibility shims only
- `metaos/runtime/`: runtime compatibility shims only
- `core/`: compatibility layer for older runtime and replay entrypoints
- `evolution/`: compatibility layer for older pressure, quest, and quota entrypoints

Canonical owners:
- `GENESIS`: canonical execution kernel for truth, replay, invariants, supervisor, dispatcher, validator
- `METAOS-A`: domain exploration unit binding goal + GENESIS + domain resources
- `METAOS-B`: exploration manager allocating budgets and scheduling multiple METAOS-A units
- `METAOS-C`: civilization engine for domain discovery, long-horizon memory, and topology
