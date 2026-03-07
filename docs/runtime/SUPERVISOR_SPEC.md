# Supervisor Specification

This document defines the centralized runtime supervisor responsible for recovery, safety, and continuity.

## Purpose

The supervisor enforces GENESIS safety law when execution, replay, or repair paths become unsafe.

## Scope

Canonical owners:
- `genesis/supervisor.py`
- `runtime/supervisor.py`
- `metaos/core/supervisor.py` as compatibility surface

## Invariants

- failure handling must preserve append-only truth
- supervisor may downshift or restore, but not mutate historical truth
- invalid state restore must be replay-backed

## Inputs

- runtime step result or raised exception
- replay state
- pressure and safety summaries

## Outputs

- safe-mode restore payload
- retry or reframing decisions
- repair escalation directives

## Event Flow

- validate runtime step
- on invalid state: restore from replay and enter safe mode
- on plateau or collapse: inject repair or reframing pressure
- on repeated failure: escalate instead of hiding the failure

## Failure Modes

- invalid state
- repair failure
- plateau
- exploration collapse
- replay restore failure

## Recovery Behavior

- invalid state -> replay restore
- replay restore failure -> explicit supervisor failure
- repair failure -> repair escalation
- plateau -> reframing or exploration shift
- diversity collapse -> anti-collapse and diversity repair actions

## Ownership

- canonical: `genesis/` and `runtime/`
- compatibility: `core/` and `metaos/core/`

## Test Mapping

- `tests/test_genesis_acceptance.py`
- `tests/test_failure_protocol.py`
- `tests/test_failure_escalation.py`
- `tests/test_runtime_safety.py`

## Operator Examples

- `metaos safety-status`
- `bash ops/validate-runtime.sh`
