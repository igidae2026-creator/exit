# Change Policy

## 1. Immutable Documents
- `docs/core/GENESIS.md` is law-level and changed only by explicit governance decision.

## 2. High-Stability Documents
- architecture ownership docs
- runtime replay/failure specifications
- operator runbook and release gates

Changes require synchronized code + tests + docs updates.

## 3. Adjustable Documents
- tactical run procedures
- tuning recommendations
- CI tier assignments

## 4. Change Approval Rules
- Any change touching canonical ownership, replay semantics, artifact immutability, or failure protocol requires:
  1. code diff
  2. invariant test updates
  3. doc truth-sync update

## 5. Documentation Update Rules
- No outline-only critical docs.
- README, RUNBOOK, and docs/operations must agree on commands and ownership.
- Release validation should fail when docs claim behavior unsupported by tests.
