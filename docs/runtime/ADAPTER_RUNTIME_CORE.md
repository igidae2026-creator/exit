# Consumer Runtime Core: Contracts, Conformance, Versioning

## Read This When

You need to know what the shared MetaOS consumer runtime owns, and what a project adapter must not re-implement.

## Shared Runtime Ownership

The shared runtime should own:

- adapter resolution
- contract version compatibility
- migration rule registration and rollout holds
- conformance matrix generation
- end-to-end adapter conformance flow
- failure-recovery verdicts

Project repositories should own only adapter normalization logic and consumer-specific boundary tests.

## Closely Related Docs

- `CONSUMER_VERSIONING.md`
- `CONSUMER_ONBOARDING_TEMPLATE.md`
- `CONSUMER_INTERVENTIONS.md`

Reference:
- `docs/runtime/RUNTIME_DOCS_INDEX.md`
- `docs/runtime/PLATFORM_LAYER_FRAMING.md`
