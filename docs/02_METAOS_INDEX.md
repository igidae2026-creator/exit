# METAOS Index

This document is the navigation hub for all METAOS specifications.

Top-level law and architecture:
- [GENESIS](docs/core/GENESIS.md)
- [METAOS Final Definition](docs/core/METAOS_FINAL_DEFINITION.md)
- [Layers](docs/architecture/LAYERS.md)
- [Boundaries](docs/architecture/BOUNDARIES.md)
- [Boundary Truth Map](docs/architecture/BOUNDARY_TRUTH_MAP.md)
- [Invariant Traceability Matrix](docs/architecture/INVARIANT_TRACEABILITY.md)
- [Why METAOS](docs/architecture/WHY_METAOS.md)

## 1. Constitutional Documents
- `docs/00_METAOS_CONSTITUTION.md`
- `docs/core/GENESIS.md`
- `docs/core/METAOS_FINAL_DEFINITION.md`

## 2. Core Specifications
- `docs/01_METAOS_MASTER_SPEC.md`
- `docs/architecture/LAYERS.md`
- `docs/architecture/BOUNDARIES.md`

## 3. Artifact Specifications
- `docs/artifact/*`
- runtime + validation artifact law tests (`tests/test_artifact_*`, `tests/test_registry_rebuildability_arch.py`)

## 4. Evolution Specifications
- `docs/evolution/*`
- runtime pressure, allocation, and quest evolution modules under `runtime/`

## 5. Runtime Specifications
- `docs/runtime/*`
- `runtime/orchestrator.py`, `runtime/core_loop.py`, `runtime/replay_state.py`

## 6. Domain Specifications
- `docs/domains/*`
- `domains/contract.py`, `domains/loader.py`, `domains/domain_genome*.py`

## 7. Civilization Specifications
- `docs/civilization/*`
- `metaos_a/`, `metaos_b/`, `metaos_c/`, `observer/`

## 8. Operations Specifications
- `docs/ops/*`
- `RUNBOOK.md`, `ops/*.sh`, `scripts/*.sh`, `metaos/cli.py`

## 9. Recommended Reading Order
1. Constitution + GENESIS
2. Master spec + boundary truth map
3. invariant traceability matrix
4. runbook and operations docs
5. runtime/domain/artifact implementation and tests
