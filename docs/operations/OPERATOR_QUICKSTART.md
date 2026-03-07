# Operator Quickstart

## Bootstrap

1. `python -m app.cli validate`
2. `python -m app.cli replay-check`
3. `python -m app.cli health`
4. `python -m app.cli long-run-check --tier smoke`

## Unbounded Run

1. `python -m app.cli run --profile production`
2. Stop only by operator action or guardrail escalation.

## Status Surfaces

- `python -m app.cli civilization-status`
- `python -m app.cli lineage-status`
- `python -m app.cli domain-status`
- `python -m app.cli pressure-status`
- `python -m app.cli economy-status`
- `python -m app.cli stability-status`
- `python -m app.cli safety-status`

## Recovery

- plateau: inspect pressure and stability, then run bounded validation
- repair escalation: inspect safety status and rotate runtime if necessary
- invalid state: replay restore from append-only truth, then rerun smoke validation
