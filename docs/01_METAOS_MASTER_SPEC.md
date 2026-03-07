# METAOS Master Specification

## 목적
GENESIS 헌법을 코드/런타임/운영 표면으로 연결하는 정식 구현 사양.

## 불변식
- Minimal core + domain autonomy 유지.
- Canonical runtime은 deprecated compatibility surface에 역의존하지 않는다.
- long-run acceptance는 profile 기준으로 상향된다.

## 상태 모델
- Core state: replayed append-only truth.
- Runtime state: pressure/economy/stability/lineage/domain/policy populations.
- Ops state: release surface, CLI contract, runbook procedures.

## 이벤트/아티팩트 스키마
- artifact manifest와 registry/event/archive 간 상호 정합성 유지.
- policy bundle은 generation/version/activation evidence를 포함.

## 실패 시나리오
- fail-open은 canonical 경로에서 기본 비활성화.
- invalid replay/append-only 위반은 validation 실패로 처리.

## 운영 절차
- 빌드: `python -m app.cli build-release`
- 릴리스 검증: `python -m app.cli validate-release`
- 장기 검증: `python -m app.cli long-run-check --tier soak`

## Acceptance Criteria
- smoke>=1024, soak>=10000, endurance>=100000 ticks.
- 건강도: smoke>=0.75, soak/endurance>=0.80.
- lineage/domain/policy 최소치 충족.

## 관련 구현 파일
- `runtime/soak_runner.py`
- `runtime/long_run_validation.py`
- `scripts/build_release_zip.sh`
- `scripts/validate_release_tree.sh`
- `pyproject.toml`

## 관련 테스트
- `tests/test_long_run_civilization_health.py`
- `tests/test_long_run_policy_evolution.py`
- `tests/test_long_run_profiles.py`
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
