# Policy Runtime

## Contract

Policies are artifacts. Registration, activation, swap, rollback, and replay visibility must all occur through artifact-backed history.

## Current Runtime

- policy bundles are registered through `runtime/policy_store.py`
- policy swaps emit append-only events
- replay reconstructs current policy ids from policy events

## Required Semantics

- hot-swap visible to replay
- rollback is another artifact selection, not mutation-in-place
- policy generations are measurable in long-run validation
