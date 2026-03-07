# METAOS Final Definition

METAOS is an autonomous exploration civilization engine governed by GENESIS, with bounded validation modes and an unbounded production mode.

Canonical loop:
- `signal -> generate -> evaluate -> select -> mutate -> archive -> repeat`

Primary operational control surface:
- `civilization_state` as replay-derived runtime state

Canonical hierarchy:
- `GENESIS -> METAOS-A -> METAOS-B -> METAOS-C`

Ownership:
- `genesis/`: kernel law, append-only truth, replay, invariants
- `runtime/`: civilization state, pressure, economy, orchestration
- `artifact/`: immutable artifact registry, archive, lineage
- `domains/`: domain logic and domain evolution helpers
- `validation/`: invariant and boundary enforcement
- `metaos_a/`: one domain exploration unit
- `metaos_b/`: cross-unit allocation and experiment selection
- `metaos_c/`: civilization memory, topology, and domain discovery

Compatibility-only surfaces:
- `core/`
- `kernel/`
- `evolution/`
- `metaos/kernel/`
- `metaos/runtime/`
- `metaos/domains/`
