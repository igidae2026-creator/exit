# Consumer Versioning

Consumer/runtime version mismatch should be handled by policy, not ad-hoc fixes.

Default rules:

- same version: `accept`
- mismatch with no migration rule: `reject`
- mismatch with registered migration rule: `hold`

Migration rules should define:

- `from_version`
- `to_version`
- `strategy`
- `steps`
- `compatibility_window`

The runtime should expose migration state in the conformance matrix so rollout risk is visible before enablement.
