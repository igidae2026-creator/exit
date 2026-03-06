# Layers

GENESIS is the top-level law. This file describes how the current codebase maps to it.

Canonical layers:
- `kernel`: [kernel/](/home/meta_os/metaos/kernel) and [metaos/kernel/](/home/meta_os/metaos/metaos/kernel)
- `runtime`: [metaos/runtime/](/home/meta_os/metaos/metaos/runtime)
- `artifact`: [artifact/](/home/meta_os/metaos/artifact)
- `domains`: [domains/](/home/meta_os/metaos/domains)
- `validation`: [validation/](/home/meta_os/metaos/validation)

Legacy compatibility surfaces:
- `core/`: compatibility layer for older runtime and replay entrypoints
- `evolution/`: compatibility layer for older pressure, quest, and quota entrypoints

METAOS-A / METAOS-B / METAOS-C:
- `METAOS-A`: law and invariants. Implemented by `docs/core/GENESIS.md`, `kernel/spine.py`, `kernel/replay.py`, `kernel/invariants.py`, `validation/*`.
- `METAOS-B`: runtime civilization. Implemented by `metaos/runtime/*`, `artifact/*`, and domain routing/economy/civilization modules.
- `METAOS-C`: legacy compatibility surface. Implemented by `core/*`, `evolution/*`, and shims preserving historical imports while converging toward the canonical boundary model.
