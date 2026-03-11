# Onboarding Checklist: Add A Consumer Without Core Edits

## Read This When

You are adding a new consumer and want the shortest path that should not require runtime-core redesign.

## Standard Flow

Use this flow for every new consumer:

1. generate scaffold
2. implement adapter normalization
3. register consumer
4. run conformance
5. verify contract version compatibility
6. add stress and recovery coverage if the domain is high-risk

## Success Condition

The target state is:

- no runtime core edits for a normal consumer addition
- adapter-only implementation
- conformance matrix inclusion
- recovery semantics inherited from the shared core

Reference:
- `docs/runtime/RUNTIME_DOCS_INDEX.md`
- `docs/runtime/ADAPTER_RUNTIME_CORE.md`
