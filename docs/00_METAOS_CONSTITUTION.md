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
- 장기 검증은 profile 기반 실행: `python -m app.cli long-run-check --profile smoke|soak|endurance`.
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
