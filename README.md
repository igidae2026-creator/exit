# METAOS

METAOS is an autonomous exploration civilization engine for replayable, pressure-driven solution evolution under GENESIS law.

Primary references:
- [GENESIS](docs/core/GENESIS.md)
- [METAOS Final Definition](docs/core/METAOS_FINAL_DEFINITION.md)
- [Architecture Layers](docs/architecture/LAYERS.md)
- [Architecture Boundaries](docs/architecture/BOUNDARIES.md)
- [Why METAOS](docs/architecture/WHY_METAOS.md)

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

Compatibility-only surfaces:
- `core/`
- `kernel/`
- `evolution/`
- `loop/`
- `metaos/kernel/`
- `metaos/runtime/`
- `metaos/domains/`

## Runtime Profiles

Runtime scale is profile-driven; demo-size constants are not canonical truth.

- `smoke`: 1,000 ticks target, 8-32 workers, >=2 lineages, >=2 domains.
- `soak`: 50,000 ticks target, 64-256 workers, >=8 lineages, >=4 domains.
- `endurance`: 500,000 ticks target, 256-1,024 workers, >=16 lineages, >=8 domains.
- `civilization`: unbounded target ticks, production guardrails/rotation/recovery playbook mode.

Select with `METAOS_RUNTIME_PROFILE` or CLI `--profile`.

## Operational Surfaces

- `python -m app.cli run --profile smoke`
- `python -m app.cli health`
- `python -m app.cli replay-check`
- `python -m app.cli civilization-status`
- `python -m app.cli lineage-status`
- `python -m app.cli domain-status`
- `python -m app.cli economy-status`
- `python -m app.cli stability-status`
- `python -m app.cli safety-status`
- `python -m app.cli long-run-check --profile smoke`
- `bash ops/run-metaos.sh`
- `bash ops/validate-runtime.sh`
- `python -m app.cli long-run-check --tier smoke`
- `python -m app.cli long-run-check --tier bounded`
- `python -m app.cli long-run-check --tier soak`
- `bash ops/run-metaos.sh`
- `bash ops/validate-runtime.sh`

## Long-Run Status

- civilization-state architecture is the live control model
- replay is append-only and deterministic under GENESIS rules
- created, active, inactive, retired, and resurrectable domains are tracked separately
- lineage health distinguishes active, dormant, zombie, and dominant lock-in cases
- economy balance is tracked independently from raw throughput
- artifact, lineage, economy, domain, stability, and safety status are observable through CLI and ops surfaces


Long-run tiers:
- smoke: minimum 256 ticks
- bounded: minimum 4096 ticks
- soak: minimum 50000 ticks
