# METAOS Master Specification

Highest-order reference:
- [GENESIS](docs/core/GENESIS.md)
- [METAOS Final Definition](docs/core/METAOS_FINAL_DEFINITION.md)

This document defines the final structural architecture, layer boundaries, and system responsibilities of METAOS.

## 1. System Overview
METAOS is a late-stage consolidation architecture. Canonical ownership remains split across `genesis/`, `runtime/`, `artifact/`, `domains/`, `validation/`, `metaos_a/`, `metaos_b/`, `metaos_c/`.

## 2. Layer Model
- Constitutional law and replay rules: `genesis/`.
- Perpetual/ bounded runtime orchestration: `runtime/` + `metaos/cli.py`.
- Artifact and lineage persistence: `artifact/`.
- Domain autonomy and genome evolution: `domains/`.
- Invariant gates and boundary checks: `validation/`.

## 3. Core Layer
`genesis/` keeps append-only truth and recovery law minimal; compatibility layers (`core/`, `kernel/`) are shim-only.

## 4. Artifact Layer
`artifact/` owns registration, lineage, archive semantics, and replay inputs.

## 5. Evolution Layer
`strategy/`, `evolution/`, and runtime evolution modules provide pressure-responsive mutation, selection, and policy artifacts.

## 6. Runtime Layer
`runtime/` owns civilization state loop and failure protocol handling. Production perpetual loop is separated from bounded run-once/long-run test modes via runtime gates.

## 7. Domain Layer
`domains/` owns contracts, loaders, mutation/recombination/crossbreed, and bounded expansion.

## 8. Civilization Layer
`metaos_a/`, `metaos_b/`, and `metaos_c/` compose one-domain unit, multi-unit scheduling, and civilization memory/topology/discovery.

## 9. Operations Layer
`app/`, `metaos/cli.py`, `ops/`, `scripts/` provide operator controls, health surfaces, release validation, and replay checks.

## 10. Cross-Layer Contracts
- Runtime may consume domain contracts but may not embed domain-specific behavior.
- Validation may inspect but never mutate runtime state.
- Observer/app must project state only.
- Compatibility surfaces must redirect, not duplicate canonical logic.

## 11. Global Invariants
Enforced by `validation/*` and tests:
- loop order, replayability, append-only truth
- artifact immutability and lineage linkage
- human/system boundary separation
- bounded vs perpetual runtime mode separation

## 12. Specification Links
- [Boundary Truth Map](docs/architecture/BOUNDARY_TRUTH_MAP.md)
- [Invariant Traceability Matrix](docs/architecture/INVARIANT_TRACEABILITY.md)
- [Operations](docs/ops/OPERATIONS.md)
- [Recovery](docs/ops/RECOVERY.md)
