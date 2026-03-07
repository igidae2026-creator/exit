# Recovery

GENESIS recovery law:
- `plateau -> exploration_collapse -> diversity_repair_failure -> repair_escalation -> invalid_state -> replay_restore`

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
- plateau: recover through reframing pressure, novelty pressure, and knowledge-guided quest regeneration
- exploration collapse: recover through diversity protection, resurrection, and domain opportunity forcing
- diversity repair failure: recover through escalation when diversity repair fails to restore ecology floors
- invalid state: recover through replay restore and safe mode
- missing artifact references: recover by replay reconstruction or explicit repair path
- corrupted derived state: discard derived state and rebuild from append-only truth

Machine-verifiable checks:
- `metaos replay-check`
- `metaos safety-status`
- `metaos long-run-check`
- `bash ops/validate-runtime.sh`
