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

Failure classes:
- plateau: recover through reframing or exploration pressure increase
- exploration collapse: recover through diversity pressure and branch forcing
- invalid state: recover through replay restore and safe mode
- missing artifact references: recover by replay reconstruction or explicit repair path
- corrupted derived state: discard derived state and rebuild from append-only truth

Machine-verifiable checks:
- `metaos replay-check`
- `metaos safety-status`
- `metaos long-run-check`
- `bash ops/validate-runtime.sh`
