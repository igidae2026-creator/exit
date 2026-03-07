# METAOS Index

## 목적
헌법-구현-테스트-운영 표면의 탐색 인덱스.

## 핵심 문서
- Constitution: `docs/00_METAOS_CONSTITUTION.md`
- Master Spec: `docs/01_METAOS_MASTER_SPEC.md`
- GENESIS law: `docs/core/GENESIS.md`
- Final Definition: `docs/core/METAOS_FINAL_DEFINITION.md`

## 런타임/운영 문서
- Runtime specs: `docs/runtime/*.md`
- Ops: `docs/ops/OPERATIONS.md`, `docs/ops/RECOVERY.md`, `docs/ops/RELEASE.md`
- Runbook: `RUNBOOK.md`

## Canonical 구현 경로
- `runtime/`: orchestrator, long-run validation, safety
- `artifact/`: immutable artifact/lineage truth
- `genesis/`: replay and invariant law
- `app/`, `metaos/cli.py`: operator surface

## 테스트 인덱스
- Replay/lineage: `tests/test_exploration_civilization.py`
- Long-run health: `tests/test_long_run_*.py`
- Docs sync/traceability: `tests/test_docs_truth_sync.py`

## 권장 검증 순서
1. `python -m app.cli validate`
2. `python -m app.cli run-once --ticks 3`
3. `python -m app.cli replay-check`
4. `python -m app.cli long-run-check --profile smoke`
5. `python -m app.cli validate-release`
