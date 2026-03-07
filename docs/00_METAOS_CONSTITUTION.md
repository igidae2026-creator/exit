# METAOS Constitution

Highest-order law:
- [GENESIS](docs/core/GENESIS.md)
- [METAOS Final Definition](docs/core/METAOS_FINAL_DEFINITION.md)

METAOS is an exploration-first system built on artifact-first principles, append-only truth, replayable state, and minimal core design.

## 1. Core Principles
- The exploration loop is mandatory and continuous in production mode.
- Human authority is limited to goal, essence, constraints, acceptance.
- System authority covers exploration, implementation, validation, evolution, expansion.
- Anything that evolves is represented as an immutable artifact with lineage.

## 2. Immutable System Rules
1. Core loop order: `signal -> generate -> evaluate -> select -> mutate -> archive -> repeat`.
2. Runtime state is reconstructed from append-only logs and archives.
3. Policies are runtime-replaceable artifacts; no policy hardcoding.
4. Multiple lineages must coexist; dominance collapse triggers repair pressure.

## 3. Forbidden Structures
- Hidden mutable state that cannot be replayed.
- Domain-specific logic inside minimal kernel/genesis core.
- Runtime mutation of archived artifacts.
- CLI/operator surfaces implementing business logic.

## 4. Exploration First
Exploration pressure is derived from novelty, diversity, efficiency, repair load, and transfer/domain shift pressure. Allocation and questing must consume this pressure model.

## 5. Artifact First
- Quest, evaluation, policy, lineage, and domain-genome outputs are first-class artifacts.
- Every mutation creates a new artifact and links parent lineage IDs.
- Archive and store are append-only inputs to replay.

## 6. Append-only Truth
Truth is written as events and artifacts only. Deletions and in-place rewrites are non-canonical maintenance operations and must not affect replay paths.

## 7. Replayable State
Replay rebuilds effective state, including policies, quest portfolio, domain genomes, lineage graph, and failure history.

## 8. Minimal Core
Core law should only encode loop orchestration, invariant enforcement, and recovery protocol; strategy/domain specialization remains outside core.

## 9. Domain Autonomy
Domains are loaded through contracts and genomes. New domains integrate via `domains/loader.py` and runtime policies without core modification.

## 10. Swarm Expansion
METAOS-A/B/C contracts:
- A: one-domain exploration unit.
- B: multi-unit scheduling and resource selection.
- C: civilization memory/topology/domain discovery.

## 11. Constitutional Priority
When docs, tests, and runtime drift, constitutional invariants and executable validation gates are source of truth.

## 12. Linked Specifications
- [Master Spec](docs/01_METAOS_MASTER_SPEC.md)
- [Index](docs/02_METAOS_INDEX.md)
- [Boundary Truth Map](docs/architecture/BOUNDARY_TRUTH_MAP.md)
- [Invariant Traceability Matrix](docs/architecture/INVARIANT_TRACEABILITY.md)
