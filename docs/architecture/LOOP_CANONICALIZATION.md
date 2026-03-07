# Loop Canonicalization

## Genesis Loop

`signal -> generate -> evaluate -> select -> mutate -> archive -> repeat`

## Derived Runtime Frame

`civilization_state -> pressure/allocation/quest/policy/domain/knowledge summaries`

## Mapping

- `signal`: replay state, truth-derived signals, and active pressure inputs
- `generate`: quest generation, policy proposal, candidate creation, domain opportunity generation
- `evaluate`: score vectors, guardrails, selection pressure, stability assessment, knowledge retrieval
- `select`: active quest and lineage choice, policy swap, allocation choice, repair path choice
- `mutate`: artifact creation, lineage branching, policy replacement, domain mutation, repair action
- `archive`: append-only log, registry, archive facts, and knowledge accumulation inputs
- `repeat`: next tick from replayed state, never by mutable hidden truth

## Enforcement

- `runtime/orchestrator.py` is the canonical execution entrypoint.
- `runtime/long_run_validation.py` is the canonical bounded validation surface.
- `runtime/genesis_ceiling.py` is the single-source ceiling owner for loop order, ecology floors, dominance caps, and failure protocol states.
- `runtime/core_loop.py` preserves legacy handler aliases but normalizes execution to the canonical stage names.
- `metaos/cli.py` and `ops/*.sh` must call these surfaces without inventing alternate stage order.
- runtime, validation, tests, docs, observer projections, and release verification must all expose the same external sequence: `signal -> generate -> evaluate -> select -> mutate -> archive -> repeat`.
