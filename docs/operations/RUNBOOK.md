# Runbook

This runbook is the operator procedure for a Genesis-faithful runtime.

## 1. First Boot
1. Create a clean runtime root: `export METAOS_RUNTIME_ROOT=$(pwd)/.metaos_runtime`.
2. Validate boundaries and replay pipeline: `python -m app.cli validate && python -m app.cli replay-check`.
3. Confirm health surfaces:
   - `python -m app.cli health`
   - `python -m app.cli civilization-status`
   - `python -m app.cli lineage-status`
   - `python -m app.cli domain-status`

## 2. Smoke Run (2,000 ticks)
Run:
- `python -m app.cli long-run-check --profile smoke --ticks 2000 --seed 42`

Required checks:
- replay remains readable (`replay_ok=true`)
- no invalid-state deadlock
- `profile_acceptance.accepted=true` if profile floors are met

## 3. Stability Run (20,000 ticks)
Run:
- `python -m app.cli long-run-check --profile stability --ticks 20000 --seed 42`

Review:
- policy/evaluation generation growth
- lineage diversity and dominance index
- active domain count and domain lifecycle distribution

## 4. Endurance Run (100,000 ticks)
Run:
- `python -m app.cli long-run-check --profile endurance --ticks 100000 --seed 42`

This run is soak-tier; execute in CI nightly/weekly, not per-commit.

## 5. Replay Audit
1. Execute run and collect artifacts.
2. Execute `python -m app.cli replay` and `python -m app.cli replay-check`.
3. Verify reconstructed tick equals latest observed tick and lineage/domain/economy summaries remain parseable.

## 6. Failure and Safe Recovery
1. Detect pressure escalation via `python -m app.cli safety-status` and `python -m app.cli stability-status`.
2. If replay fails or invalid state is detected:
   - rotate runtime files (`bash ops/rotate-runtime.sh`)
   - replay-check again
   - run smoke profile before resuming continuous run
3. If repeated repair escalation appears, run `bash ops/cleanup-runtime.sh`, then restore from append-only logs and rerun replay check.

## 7. Release Preparation
1. `python -m app.cli build-release`
2. `python -m app.cli validate-release`
3. `bash ops/validate-runtime.sh`

Release candidate must include replayable truth, immutable artifacts, and non-placeholder operator docs.
