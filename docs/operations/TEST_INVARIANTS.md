# Test Invariants

These invariants are required in CI and release validation.

## 1. Append-only Invariant
- Event, metrics, and registry logs are append-only.
- Mutation of historical entries is test failure.

## 2. Replay Determinism
- Replaying identical logs returns identical effective state.
- Replay check must fail on corrupted input, not degrade silently.

## 3. Lineage Integrity
- Every generated artifact links to a lineage id.
- Branch/retire/reactivate transitions are auditable.

## 4. Domain Contract
- Domain artifacts satisfy required contract fields.
- Invalid domains are quarantined and never become canonical owners.

## 5. Supervisor Safety
- Invalid-state injection forces safe mode and replay restore.
- Hard failure recovery resumes safe progress within bounded ticks.

## 6. Anti-Collapse
- Dominance index and diversity pressure guardrails trigger before lock-in.
- Long-run checks require multi-lineage survival and multi-domain activity.
