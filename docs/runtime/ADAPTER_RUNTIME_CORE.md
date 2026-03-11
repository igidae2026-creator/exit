# Adapter Runtime Core

This document fixes the generic MetaOS adapter runtime core.

The shared runtime should own:

- adapter resolution
- contract version compatibility
- migration rule registration and rollout holds
- conformance matrix generation
- end-to-end adapter conformance flow
- failure-recovery verdicts

Project repositories should own only adapter normalization logic.

Reference:
- `docs/runtime/PLATFORM_LAYER_FRAMING.md`
