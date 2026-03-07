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
- 장기 검증: `python -m app.cli long-run-check --profile soak`

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
