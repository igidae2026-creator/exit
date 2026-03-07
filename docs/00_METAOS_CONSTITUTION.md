# METAOS Constitution

## 목적
이 문서는 METAOS의 최상위 운영 헌법이며, GENESIS 법을 구현 레벨로 강제하기 위한 불변 계약을 정의한다.

## 불변식
1. 탐색 루프는 기본적으로 연속(무기한) 실행이어야 한다.
2. 모든 진화 산출물은 immutable artifact + lineage로 기록되어야 한다.
3. truth 로그(events/registry/archive/metrics)는 append-only 여야 한다.
4. 동일 seed/입력/artifact 집합에서 replay digest는 결정론적으로 동일해야 한다.
5. human 입력은 goal/essence/constraints/acceptance 로 제한된다.

## 상태 모델
- `civilization_state`: pressure/allocation/quest/artifact/domain/memory를 묶는 운영 상태.
- `runtime_safety`: safe/degraded/recovery 모드와 가드레일 개입 이력.
- `lineage/domain registry`: 생존/휴면/은퇴/부활 상태.

## 이벤트/아티팩트 스키마
- 이벤트: `timestamp`, `event_type`, `payload`, `schema_version`.
- 아티팩트: `artifact_id`, `kind`, `payload_hash`, `parent_ids`, `metadata.lineage_id`, `tick`.
- replay envelope: tick, lineage/domain summary, policy generation snapshot.

## 실패 시나리오
- plateau -> exploration collapse -> diversity repair failure -> escalation -> invalid state -> replay restore 순서로 복구.
- replay mismatch, artifact mutation, lineage breakage는 hard fail.

## 운영 절차
- 기본 런타임은 unbounded 실행: `python -m app.cli run`.
- 장기 검증은 tier 기반 실행: `python -m app.cli long-run-check --tier smoke|bootstrap|aggressive|soak`.
- 운영자는 health/status/replay/safety를 주기적으로 검증.

## Acceptance Criteria
- autonomous loop, artifact lineage evolution, full replay reconstruction, failure recovery,
  runtime policy evolution, multiple lineage survival, core 수정 없는 domain 확장 실증.

## 관련 구현 파일
- `runtime/orchestrator.py`
- `runtime/long_run_validation.py`
- `metaos/cli.py`

## 관련 테스트
- `tests/test_exploration_civilization.py`
- `tests/test_long_run_ops.py`
- `tests/test_long_run_multi_lineage.py`
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
