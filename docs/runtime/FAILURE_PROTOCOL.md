# Failure Protocol

Owner: `runtime/genesis_ceiling.py`, `runtime/runtime_safety.py`, `runtime/long_run_validation.py`

State model:
- `plateau`
- `exploration_collapse`
- `diversity_repair`
- `repair_escalation`
- `invalid_state`
- `replay_restore`
- `safe_mode`
- `resume`

Event schema:
- `trigger`: observed runtime condition
- `observable_reason`: ecology, replay, or repair signal that caused the transition
- `replay_consequence`: whether replay restore, safe mode, or normal resume is required

Replay semantics:
- failure transitions are derived from append-only truth and must be replay-stable
- replay digest corruption or invalid reconstruction forces `replay_restore`
- observer projections may be regenerated, but append-only truth must not be rewritten

## Canonical Triggers

- plateau -> exploration pressure and reframing
- collapse -> diversity repair
- diversity repair failure -> repair escalation
- invalid state -> replay restore
- dominance `> 0.45` -> diversity repair and dormant lineage resurrection
- active lineages `< 8` or active domains `< 4` -> exploration collapse

## Runtime Handling

- repairs emit repair artifacts
- safe mode is explicit, observable, and lineage-preserving
- replay restore is the final authority for invalid state recovery
- runtime safety exposes the current `failure_protocol_state`
- long-run validation records ceiling alignment against the same thresholds

## Runtime Interface

- `python -m metaos.cli safety-status`
- `python -m metaos.cli replay-check`
- `python -m metaos.cli long-run-check --tier smoke|bootstrap|aggressive|soak`
- observer/status surfaces must expose the same canonical state names without aliases

## Operator Handling

- inspect `safety-status` and `stability-status`
- run `replay-check`
- rotate runtime only after append-only truth is preserved
- rerun `long-run-check --tier smoke` after restore

## Operator Commands

- validate runtime contract: `python -m metaos.cli validate`
- inspect current failure state: `python -m metaos.cli safety-status`
- verify replay restore path: `python -m metaos.cli replay-check`
- run bounded release verification: `python -m metaos.cli --max-ticks 1 run-once --ticks 1`

## Test Obligations

- tests must assert the canonical state set remains exactly `plateau`, `exploration_collapse`, `diversity_repair`, `repair_escalation`, `invalid_state`, `replay_restore`, `safe_mode`, `resume`
- tests must validate lineage floor `< 8`, domain floor `< 4`, and dominance emergency `> 0.45` transitions
- release verification must confirm CLI, replay, and documentation surfaces agree on the same state names
