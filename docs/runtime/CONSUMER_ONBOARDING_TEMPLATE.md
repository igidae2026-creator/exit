# Consumer Onboarding Template

Use this flow for every new consumer:

1. generate scaffold
2. implement adapter normalization
3. register consumer
4. run conformance
5. verify contract version compatibility
6. add stress and recovery coverage if the domain is high-risk

The target state is:

- no runtime core edits for a normal consumer addition
- adapter-only implementation
- conformance matrix inclusion
- recovery semantics inherited from the shared core
