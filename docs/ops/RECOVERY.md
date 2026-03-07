# Recovery

GENESIS recovery law:
- invalid state -> replay restore
- repair failure -> repair escalation
- plateau -> exploration or reframing
- collapse -> diversity pressure

Operator steps:
- `python -m app.cli replay-check`
- `python -m app.cli stability-status`
- `python -m app.cli safety-status`
- `python -m app.cli long-run-check`
- `bash ops/rotate-runtime.sh`
- `bash ops/cleanup-runtime.sh`
- `bash ops/run-metaos.sh`

Recovery truth:
- replay remains append-only
- artifacts remain immutable
- civilization_state is reconstructed from append-only truth and replayed effective state
- operators intervene only when guardrails keep firing, replay fails, or long-run health drops
