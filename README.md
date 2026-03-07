# METAOS

METAOS is a bounded autonomous exploration civilization engine. It is for replayable, pressure-driven solution evolution under GENESIS law, not for one-shot task execution.

Primary references:
- [GENESIS](/home/meta_os/metaos/docs/core/GENESIS.md)
- [METAOS Final Definition](/home/meta_os/metaos/docs/core/METAOS_FINAL_DEFINITION.md)
- [Architecture Layers](/home/meta_os/metaos/docs/architecture/LAYERS.md)
- [Architecture Boundaries](/home/meta_os/metaos/docs/architecture/BOUNDARIES.md)
- [Why METAOS](/home/meta_os/metaos/docs/architecture/WHY_METAOS.md)

## What METAOS Is

METAOS is organized around `civilization_state` as the primary control surface.

Canonical control flow:
- `civilization_state`
- `-> pressure`
- `-> allocation`
- `-> questing`
- `-> artifact evolution`
- `-> domain evolution`
- `-> memory accumulation`

Canonical hierarchy:
- `GENESIS -> METAOS-A -> METAOS-B -> METAOS-C`

Canonical ownership:
- `genesis/`: truth, replay, invariants, supervisor law
- `runtime/`: civilization state, pressure, allocation, orchestration
- `artifact/`: immutable artifact registry, archive, lineage
- `domains/`: domain logic, genomes, recombination, mutation
- `validation/`: invariant law and boundary enforcement
- `metaos_a/`: one domain exploration unit
- `metaos_b/`: multi-unit scheduling and resource selection
- `metaos_c/`: civilization memory, topology, domain discovery

Deprecated surfaces are compatibility-only:
- `core/`
- `kernel/`
- `evolution/`
- `metaos/kernel/`
- `metaos/runtime/`
- `metaos/domains/`

## Why Use METAOS

- when solutions must evolve over long runs instead of being hand-scripted up front
- when append-only truth and replayable effective state matter
- when multiple lineages and bounded domain expansion matter
- when operators need observable economy, lineage, domain lifecycle, stability, safety, and replay status

## When Not To Use METAOS

- when a single-shot assistant or workflow engine is enough
- when replay and artifact lineage do not matter
- when you do not want automatic exploration, validation, and expansion

## What An Operator Does

- defines goal, essence, constraints, and acceptance
- starts and validates the runtime
- observes civilization, lineage, domain, economy, and replay status
- observes long-horizon stability, domain retirement/resurrection pressure, and guardrail interventions
- rotates and cleans runtime state safely

## What Remains Automatic

- exploration
- implementation
- validation
- policy and evaluation evolution
- bounded domain discovery
- memory accumulation
- replay-compatible continuation

## Operational Surfaces

- `python -m app.cli run`
- `python -m app.cli health`
- `python -m app.cli replay-check`
- `python -m app.cli civilization-status`
- `python -m app.cli lineage-status`
- `python -m app.cli domain-status`
- `python -m app.cli economy-status`
- `python -m app.cli stability-status`
- `python -m app.cli safety-status`
- `python -m app.cli long-run-check`
- `bash ops/run-metaos.sh`
- `bash ops/validate-runtime.sh`

## Long-Run Status

- civilization-state architecture is the live control model
- replay is append-only and deterministic under GENESIS rules
- created, active, inactive, retired, and resurrectable domains are tracked separately
- lineage health distinguishes active, dormant, zombie, and dominant lock-in cases
- economy balance is tracked independently from raw throughput
- artifact, lineage, economy, domain, stability, and safety status are observable through CLI and ops surfaces
