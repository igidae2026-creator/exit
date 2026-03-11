# METAOS Agents

This repository is converged around four ownership streams and one integration rule: Genesis wins over local drift.

## Canonical Owners

- `genesis/`: append-only truth, replay law, invariant law, recovery law
- `runtime/`: `civilization_state`, pressure, allocation, questing, orchestration, long-run validation
- `artifact/`: immutable artifact registry, archive, lineage, replayable provenance
- `domains/`: domain contract, genomes, mutation, recombination, onboarding
- `validation/`: constitution, system boundary, artifact law, release truth
- `metaos_a/`: one-domain exploration unit
- `metaos_b/`: multi-unit scheduling, allocation, selection
- `metaos_c/`: civilization memory, topology, domain discovery, meta-exploration

## Support Surfaces

- `app/`: public CLI shim only
- `metaos/`: canonical installed package and CLI owner
- `observer/`: read-only operator projections
- `ops/`, `scripts/`: operator and release tooling
- `docs/`: normative truth synchronized with code

## Compatibility Surfaces

- `core/`, `kernel/`, `evolution/`, `loop/`, `metaos/kernel/`, `metaos/runtime/`, `metaos/domains/`
- These remain shims or compatibility bridges. They must not regain canonical business logic.

## Integration Rule

- Human defines goals, essence, constraints, and acceptance.
- System evolves artifacts and policies under append-only truth.
- Production runtime must remain explicitly unbounded unless an operator supplies a bound.
- New domains integrate through contracts and onboarding, not core edits.
- `docs/AUTONOMY_TARGET.md` defines the unattended execution standard for operator involvement and quality preservation.
- Preferred autonomy substrate: append-only event log, typed snapshots, job queue, and supervisor as the four core primitives, with policy layered on top.
- Do not treat loop-plus-state-file-plus-background-execution alone as sufficient architecture for 24-hour autonomous quality claims.
