# Layers

GENESIS is the top-level law.

Canonical hierarchy:
- `GENESIS -> METAOS-A -> METAOS-B -> METAOS-C`

Canonical layers:
- `genesis/`: kernel law, replay, truth spine
- `runtime/`: civilization-state owner and stage composition owner
- `artifact/`: immutable artifact and archive owner
- `domains/`: domain logic owner
- `validation/`: invariant and boundary owner
- `metaos_a/`: one domain exploration unit
- `metaos_b/`: multi-unit exploration manager
- `metaos_c/`: civilization engine
- `app/`: CLI and operator entrypoints only

Canonical loop:
- `signal -> generate -> evaluate -> select -> mutate -> archive -> repeat`

Derived runtime frame:
- `civilization_state` is the replay-derived runtime aggregate consumed by runtime, observer, and CLI surfaces

Compatibility-only layers:
- `core/`
- `kernel/`
- `evolution/`
- `metaos/kernel/`
- `metaos/runtime/`
- `metaos/domains/`
