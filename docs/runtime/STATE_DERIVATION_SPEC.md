# State Derivation Specification

This document defines how effective runtime state is derived from replayed events and artifact records.

## Purpose

Derived state turns append-only truth into the live `civilization_state` control frame.

## Scope

Canonical owners:
- `runtime/civilization_state.py`
- `runtime/civilization_memory.py`
- `runtime/pressure_derivation.py`
- `runtime/observability.py`

## Invariants

- no hidden mutable state outside append-only truth and replay-derived summaries
- derived state may be discarded and rebuilt at any time
- federation, ecosystem, lineage, domain, and evaluation metrics must remain replay-reconstructible

## Inputs

- replay state
- memory window and metrics window
- domain lifecycle state
- guardrail state
- federation state

## Outputs

- `civilization_state`
- stability, safety, and observability summaries
- lineage, domain, evaluation, federation, and hydration counters

## Event Flow

- replay append-only truth
- merge bounded recent windows
- derive populations, diversity, economy balance, and stability scores
- expose read-only projections through observer and CLI

## Failure Modes

- stale derived state
- inconsistent domain or lineage accounting
- invalid federation counters
- missing runtime frame inputs

## Recovery Behavior

- rebuild from replay and memory windows
- clamp bounded scores instead of trusting invalid values
- escalate through runtime safety and guardrails when divergence persists

## Ownership

- canonical: `runtime/`
- observer and `app/` remain read-only consumers

## Test Mapping

- `tests/test_civilization_state_fields.py`
- `tests/test_stability_observability.py`
- `tests/test_federation_live_state.py`
- `tests/test_long_run_civilization_health.py`

## Operator Examples

- `metaos civilization-status`
- `metaos economy-status`
- `metaos stability-status`
