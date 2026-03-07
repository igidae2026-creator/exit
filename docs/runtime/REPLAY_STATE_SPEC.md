# Replay State Specification

This document defines how runtime state is reconstructed from append-only logs.

## Purpose

Replay reconstructs effective state from append-only truth without trusting cached mutable state.

## Scope

Canonical owners:
- `genesis/replay.py`
- `runtime/replay_state.py`
- `genesis/spine.py`

## Invariants

- truth is append-only
- derived state is disposable
- replay on identical logs must produce identical terminal state and state hash
- mirrored federation artifacts must remain distinguishable from local artifacts

## Inputs

- `events.jsonl`
- `metrics.jsonl`
- `artifact_registry.jsonl`
- `archive/archive.jsonl`
- `signals.jsonl`
- `federation/events.jsonl` when federation is enabled

## Outputs

- tick, events, metrics, artifacts, signals
- active policies and quest state
- lineage state and civilization state
- pressure, routing, economy, recovery, signal, and federation replay state

## Event Flow

- read append-only logs
- reconstruct artifact envelopes
- rebuild lineage and civilization counters
- derive pressure, routing, economy, recovery, signals, federation state
- emit replay state hashable terminal payload

## Failure Modes

- missing or corrupted derived state
- truncated or malformed jsonl lines
- replay-visible missing artifact references
- invalid state requiring safe-mode restore

## Recovery Behavior

- ignore malformed lines, never mutate the source logs
- rebuild effective state from remaining append-only truth
- rely on supervisor restore path when runtime state becomes invalid

## Ownership

- canonical: `genesis/`
- compatibility: `kernel/`, `metaos/kernel/`, `core/replay.py`

## Test Mapping

- `tests/test_replay_determinism.py`
- `tests/test_federation_replay.py`
- `tests/test_registry_rebuildability_arch.py`
- `tests/test_release_install.py`

## Operator Examples

- `metaos replay-check`
- `python -m app.cli replay`
- `bash ops/validate-runtime.sh`
