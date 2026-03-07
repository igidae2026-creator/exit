# METAOS

METAOS is an autonomous exploration civilization engine for replayable, pressure-driven solution evolution under GENESIS law.

Primary references:
- [GENESIS](docs/core/GENESIS.md)
- [METAOS Final Definition](docs/core/METAOS_FINAL_DEFINITION.md)
- [Architecture Layers](docs/architecture/LAYERS.md)
- [Architecture Boundaries](docs/architecture/BOUNDARIES.md)
- [Why METAOS](docs/architecture/WHY_METAOS.md)
- [Ownership Matrix](docs/architecture/OWNERSHIP_MATRIX.md)

Boundary truth map:
- `docs/architecture/BOUNDARY_TRUTH_MAP.md`

Invariant traceability:
- `docs/architecture/INVARIANT_TRACEABILITY.md`

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
- `federation/`: optional bounded cross-node exchange, adoption, transport, hydration
- `ecosystem/`: optional ecosystem-scale discovery, clustering, market, knowledge network
- `observer/`: read-only projection surfaces for operators and CLI
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

Repo-only surfaces:
- `metaos-build-prompts/`
- `.github/`

Machine-readable ownership truth:
- `validation/ownership_manifest.json`

## Runtime Profiles

Runtime scale is profile-driven; demo-size constants are not canonical truth.

- `smoke`: 256 tick minimum, 1,000 tick target, 8-32 workers, >=4 surviving lineages, >=3 domains
- `bootstrap`: 1,000 tick bounded startup ecology proof
- `aggressive`: 5,000 tick bounded local validation with stricter ecology floors
- `soak`: 50,000 tick long-run stability check, 64-256 workers, >=8 surviving lineages, >=4 domains
- `production`: unbounded canonical runtime until explicit operator stop or guardrail stop
- `civilization`: compatibility alias for `production`
- `endurance`: explicit very-long bounded stress profile

Select with `METAOS_RUNTIME_PROFILE` or CLI `--profile`.

## Operational Surfaces

- installed console script: `metaos`
- `python -m app.cli run`
- `python -m app.cli health`
- `python -m app.cli replay-check`
- `python -m app.cli civilization-status`
- `python -m app.cli lineage-status`
- `python -m app.cli domain-status`
- `python -m app.cli economy-status`
- `python -m app.cli stability-status`
- `python -m app.cli safety-status`
- `python -m app.cli long-run-check --tier smoke`
- `python -m app.cli long-run-check --tier bounded`
- `python -m app.cli long-run-check --tier soak`
- `bash ops/run-metaos.sh`
- `bash ops/validate-runtime.sh`

Public installed CLI commands:
- `metaos health`
- `metaos replay-check`
- `metaos civilization-status`
- `metaos lineage-status`
- `metaos domain-status`
- `metaos pressure-status`
- `metaos economy-status`
- `metaos stability-status`
- `metaos safety-status`
- `metaos long-run-check`
- `metaos build-release`
- `metaos validate-release`

Release truth:
- wheel/install truth is defined by `pyproject.toml`
- source release truth is defined by `validation/ownership_manifest.json`
- `scripts/build_release_zip.sh` and `scripts/validate_release_tree.sh` consume the same manifest

## Long-Run Status

- civilization-state architecture is the live control model
- replay is append-only and deterministic under GENESIS rules
- created, active, inactive, retired, and resurrectable domains are tracked separately
- lineage health distinguishes active, dormant, zombie, and dominant lock-in cases
- economy balance is tracked independently from raw throughput
- artifact, lineage, economy, domain, stability, and safety status are observable through CLI and ops surfaces

Long-run tiers:
- smoke: minimum 256 ticks
- bootstrap: minimum 1000 ticks
- bounded: minimum 4096 ticks
- aggressive: minimum 5000 ticks
- soak: minimum 50000 ticks
