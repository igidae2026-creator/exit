# Failure Protocol

## Canonical Triggers

- plateau -> exploration pressure and reframing
- collapse -> diversity repair
- diversity repair failure -> repair escalation
- invalid state -> replay restore

## Runtime Handling

- repairs emit repair artifacts
- safe mode is explicit, observable, and lineage-preserving
- replay restore is the final authority for invalid state recovery

## Operator Handling

- inspect `safety-status` and `stability-status`
- run `replay-check`
- rotate runtime only after append-only truth is preserved
- rerun `long-run-check --tier smoke` after restore
