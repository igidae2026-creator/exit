# Replay State Specification

## 1. Replay Philosophy
Replay is the only legal reconstruction path for effective state. In-memory shortcuts are non-authoritative.

## 2. Source of Truth
- append-only event streams
- append-only metrics
- immutable artifact registries
- archived lifecycle records

## 3. Replay Inputs
Minimum input set:
- event log entries
- metrics log entries
- artifact registry entries (policy/domain/evaluation/artifact)
- archive entries for retirements/reactivations

## 4. Replay Process
1. Read append-only streams in commit order.
2. Rebuild control state (tick, quest, pressure, recovery mode).
3. Rebuild civilization summary (lineages/domains/economy/stability).
4. Emit deterministic projection payloads.

## 5. Derived State Rules
- Derived state must be reproducible from logs only.
- Missing log segments are hard failures.
- Non-deterministic fields are forbidden in replay output.

## 6. Determinism Rules
- Same input logs + same replay code => same reconstructed state.
- Replay check in CLI must fail hard on malformed inputs.

## 7. Replay Failure Handling
- replay parse error => unhealthy status + recovery mode
- invalid state checkpoint => restore from last valid append-only segment
- repeated replay failure => rotate runtime files, preserve immutable registries, rerun replay-check
