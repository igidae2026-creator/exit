# Genesis-Faithful Full Remediation Audit

## 1) Executive Gap Map (Top 25)
1. **Critical**: long-run defaults bounded at 120 ticks; under-tests collapse/replay drift (`metaos/cli.py`, `runtime/long_run_validation.py`, `ops/validate-runtime.sh`).
2. **Critical**: domain expansion defaults capped to 1/new window, high evidence threshold (`runtime/domain_expansion_policy.py`).
3. **Critical**: outline-only operator docs block executable operations (`docs/operations/*.md`, `docs/runtime/*.md`).
4. **Critical**: package version `0.0.0` signals prototype packaging (`pyproject.toml`, `setup.py`).
5. **High**: CLI default domain fixed to `code_domain` (single-domain behavior bias) (`metaos/cli.py`, `runtime/orchestrator.py`).
6. **High**: recovery/restore criteria not codified into profile acceptance outputs (`runtime/long_run_validation.py`).
7. **High**: replay acceptance binary not tied to horizons (`runtime/long_run_validation.py`, `tests/*long_run*`).
8. **High**: policy/evaluation generation targets not enforced in ops checks (`ops/validate-runtime.sh`).
9. **High**: docs lack hard operator recovery drill for invalid artifacts/domains (`docs/runtime/RUNTIME_FAILURE_HANDLING.md`).
10. **High**: docs and ops did not expose profile tiers smoke/stability/endurance (`docs/operations/RUNBOOK.md`).
11. **High**: no explicit gate for dominance index ceiling in release checks (`runtime/long_run_validation.py`).
12. **High**: default runtime still optimized for short-loop local smoke (`runtime/orchestrator.py`, CLI flags).
13. **Medium**: acceptance language for lineage/domain floors was implicit, not explicit (`runtime/long_run_validation.py`).
14. **Medium**: docs lacked clear immutable/high-stability/editable change classes (`docs/operations/CHANGE_POLICY.md`).
15. **Medium**: test-invariant document non-executable outline state (`docs/operations/TEST_INVARIANTS.md`).
16. **Medium**: replay spec did not define deterministic hard-fail behavior (`docs/runtime/REPLAY_STATE_SPEC.md`).
17. **Medium**: runbook did not define first-boot through release path (`docs/operations/RUNBOOK.md`).
18. **Medium**: stability checklist lacked binary release gates (`docs/operations/STABILITY_CHECKLIST.md`).
19. **Medium**: long-run command lacked profile-specific semantic targets (`metaos/cli.py`).
20. **Medium**: ops script did not pass profile context to long-run checks (`ops/validate-runtime.sh`).
21. **Medium**: policy evolution/evaluation parity only observed, not contract-driven (`runtime/long_run_validation.py`).
22. **Low**: docs lacked cross-tier CI recommendations by horizon (`docs/operations/*`).
23. **Low**: compatibility shim ownership messaging inconsistent across docs (`docs/ops/*.md`, root docs).
24. **Low**: horizon naming inconsistent in docs vs command surface (`docs/*`, CLI).
25. **Low**: domain resurrection/discovery counts not standardized in runbook acceptance text (`docs/operations/RUNBOOK.md`).

## 2) Aggressive Target Table
- Long-run smoke: `120 -> 2000` ticks; old horizon misses slow collapse; mitigated by profile tiers.
- Long-run stability: `ad-hoc -> 20000` ticks; old checks insufficient for ecology drift; mitigated by medium-tier CI.
- Long-run endurance: `none -> 100000` ticks; needed for replay durability and long ecology dynamics; mitigated by soak/nightly scheduling.
- Domain spawn cap: `1 -> 3` per decision window; old cap enforces symbolic expansion; mitigate with evidence/cooldown guards.
- Evidence threshold: `0.62 -> 0.45`; old threshold over-conservative; mitigate with guardrails and active-domain ratio checks.
- Spawn cooldown: `12 -> 3`; old cooldown throttles adaptation; mitigate by bounded budget and diversity checks.
- Package version: `0.0.0 -> 0.4.0rc1`; old version blocks release truth; mitigate with explicit prerelease tag.

## 3) File-by-File Remediation Plan
### runtime/
- `runtime/long_run_validation.py`: add horizon/profile constants and profile acceptance contracts.
- `runtime/domain_expansion_policy.py`: aggressive multi-domain defaults and higher target-domain ceiling.

### metaos/
- `metaos/cli.py`: long-run profiles (`smoke/stability/endurance`), profile-driven default ticks, less code-domain-centric default.

### ops/
- `ops/validate-runtime.sh`: profile-aware long-run invocation, 2000-tick default.

### docs/operations/
- `CHANGE_POLICY.md`, `RUNBOOK.md`, `STABILITY_CHECKLIST.md`, `TEST_INVARIANTS.md`: replace outlines with executable operator text.

### docs/runtime/
- `REPLAY_STATE_SPEC.md`, `RUNTIME_FAILURE_HANDLING.md`: convert to normative specs.

### packaging
- `pyproject.toml`, `setup.py`: bump to meaningful prerelease version.

### reviews/
- `docs/reviews/GENESIS_FULL_REMEDIATION_AUDIT.md`: unified remediation plan and acceptance contract.

## 4) Implementation Patch Plan
1. Introduce long-run profiles and floors in runtime validation.
2. Wire CLI + ops to profile-aware horizons.
3. Raise domain-expansion defaults for adaptive multi-domain operation.
4. Convert critical skeleton docs to executable guidance.
5. Bump package version for release candidate semantics.
6. Extend tests for profile acceptance and domain-expansion defaults.

Migration:
- Existing `--ticks` remains supported.
- New `--profile` is additive.
- env vars in `ops/validate-runtime.sh`: `METAOS_LONG_RUN_PROFILE` added (defaults to `smoke`).

## 5) Test Expansion Plan
- Add fast tests for profile floor object presence (`profile_acceptance`).
- Add targeted tests for domain expansion default constants.
- Add medium-tier tests for 2000-tick replay invariants.
- Add soak-tier jobs for 20k/100k tick replay and dominance checks.
- Add docs truth-sync checks for runbook command coverage.

## 6) Docs Completion Plan
Complete all prior outline-only critical docs under:
- `docs/operations/`
- `docs/runtime/`

Required contents:
- exact command lines
- binary pass/fail checks
- recovery escalation sequence
- release gate mapping to runtime outputs

## 7) Final Acceptance Contract
Binary gates:
- Genesis compliance: no canonical ownership regressions.
- Replay correctness: replay-check succeeds across smoke/stability/endurance.
- Artifact immutability: append-only and immutable envelope checks pass.
- Multi-lineage survival: profile floors met.
- Multi-domain expansion: profile floors met.
- Policy/evaluation evolution: profile floors met.
- Recovery behavior: safe-mode restore and replay restore pass.
- CLI/ops usability: runbook commands execute with documented flags.
- Release readiness: build-release + validate-release + long-run smoke pass.

## 8) Implementation Status
This patch applies immediate uplift for horizons, domain expansion defaults, packaging versioning, and critical docs.
Further work: expand automated tests to enforce new profile floors at CI tier boundaries.
