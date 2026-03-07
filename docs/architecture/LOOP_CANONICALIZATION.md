# Loop Canonicalization

## Genesis Loop

`signal -> generate -> evaluate -> select -> mutate -> archive -> repeat`

## Runtime Control Flow

`civilization_state -> pressure -> allocation -> questing -> artifact evolution -> domain evolution -> memory accumulation`

## Mapping

- `signal`: replay state, signals, and current civilization pressure inputs
- `generate`: quest generation, policy proposal, domain expansion candidates
- `evaluate`: score vectors, guardrails, selection pressure, stability assessment
- `select`: active quest and lineage choice, policy swap, allocation choice
- `mutate`: artifact creation, lineage branching, domain mutation, repair action
- `archive`: append-only log, registry, archive snapshots as derived caches
- `repeat`: next tick from replayed state, never by mutable hidden truth

## Enforcement

- `runtime/orchestrator.py` is the canonical execution entrypoint.
- `runtime/long_run_validation.py` is the canonical bounded validation surface.
- `metaos/cli.py` and `ops/*.sh` must call these surfaces without inventing alternate stage order.
