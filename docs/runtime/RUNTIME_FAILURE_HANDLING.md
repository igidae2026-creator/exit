# Runtime Failure Handling

This document defines failure handling procedures at the runtime layer.

## Purpose

Runtime failure handling keeps the exploration loop alive without weakening replay, artifact, or domain law.

## Scope

Canonical owners:
- `runtime/runtime_safety.py`
- `runtime/self_tuning_guardrails.py`
- `runtime/repair_system.py`
- `runtime/long_run_validation.py`

## Invariants

- the exploration loop must continue unless replay or truth law is broken
- failures must emit structured actions and bounded diagnostics
- recovery must never rewrite append-only truth

## Inputs

- safety metrics
- pressure frame
- federation and ecosystem pressure
- replay state
- long-run validation diagnostics

## Outputs

- `safety_actions`
- guardrail actions and tuned thresholds
- repair escalation directives
- operator-visible failure diagnostics

## Event Flow

- detect pressure, collapse, replay, storage, federation, and hydration failures
- derive bounded guardrail actions
- escalate when repeated failures persist
- expose structured diagnostics through CLI and ops surfaces

## Failure Modes

- plateau
- exploration collapse
- invalid state
- missing artifact references
- domain explosion
- policy cascade
- mirror storm
- foreign monoculture

## Recovery Behavior

- replay restore for invalid state
- repair escalation for repeated repair failure
- diversity repair for lineage collapse
- domain throttling for expansion overload
- transport and hydration throttling for federation overload or mirror storms

## Ownership

- canonical: `runtime/`
- observer and CLI surfaces are read-only

## Test Mapping

- `tests/test_runtime_safety.py`
- `tests/test_federation_monoculture_guard.py`
- `tests/test_guardrail_diversification.py`
- `tests/test_long_run_civilization_health.py`

## Operator Examples

- `metaos safety-status`
- `metaos long-run-check`
- `bash ops/validate-runtime.sh`
