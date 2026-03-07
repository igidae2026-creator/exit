# METAOS 1-Task / 4-Agent Code + Architecture Review (Consolidated)

## 1. Executive Summary

This review found that the repository already has a strong canonical direction (`genesis/`, `runtime/`, `artifact/`, `domains/`, `validation/`) but remains operationally inconsistent due to unresolved convergence work:

- The declared baseline set in the request is incomplete in-repo (`Genesis.md`, `SYSTEM_BASELINE_v1`, `MASTER_CONTRACT.md`, `ARCHITECTURE_OVERVIEW.md` are missing as exact paths), so policy anchoring is currently split between `docs/core/GENESIS.md`, `docs/architecture/*`, and runtime code.
- The single-state vision is only partially realized: `runtime.civilization_state.civilization_state()` is effectively canonical, but parallel state classes in `metaos_a`, `metaos_b`, and `metaos_c` plus `genesis.state_machine.tick_phase()` and `runtime.replay_state.ReplayState` continue to operate as quasi-independent state machines.
- Runtime integration is not stable: canonical `runtime/oed_orchestrator.py` depends on non-existent `metaos.archive.*` modules, causing test-collection-wide import failure.
- Role-boundary separation required by Level3 (DecisionCore vs Executor vs Gate/Risk vs Eval vs Assimilation) is not encoded explicitly in contracts, package boundaries, or enforcement checks.
- Optimization/scaling subsystems are present but under-scoped and conservative (small tick limits, low portfolio breadth, low archive pressure ceilings, limited budget escalation), with no explicit “stability upper-bound exploration” parameter profile.

Primary recommendation: preserve current architecture philosophy, but perform additive convergence via (1) canonical state unification, (2) import-path correction and deprecation cleanup, (3) explicit Level3 role contracts + validators, and (4) expanded exploration parameters guarded by replay/safety gates.

## 2. Canonical Baseline (what remains authoritative)

### 2.1 Authoritative documents to keep as baseline anchors

1. `docs/core/GENESIS.md` (top-level law + control loop).
2. `docs/architecture/LAYERS.md` (package hierarchy + canonical ownership).
3. `docs/architecture/BOUNDARIES.md` (forbidden crossings + compatibility surface policy).
4. `docs/architecture/DEPRECATED_FILES.md` (convergence and shim policy).

### 2.2 Baseline document gaps to close immediately

The following requested baseline files do not exist at repository root and must be added as aliases/manifests (not philosophical rewrites):

- `Genesis.md` (missing)
- `SYSTEM_BASELINE_v1` (missing)
- `MASTER_CONTRACT.md` (missing)
- `ARCHITECTURE_OVERVIEW.md` (missing)

Create each as a thin canonical pointer to current authoritative docs to prevent contract drift.

## 3. Files / modules to keep as core

Keep these as core execution/control owners (authoritative runtime path):

- `genesis/`
  - `genesis/contracts.py`
  - `genesis/replay.py`
  - `genesis/event_log.py`
  - `genesis/invariants.py`
  - `genesis/supervisor.py`
- `runtime/`
  - `runtime/orchestrator.py`
  - `runtime/supervisor.py`
  - `runtime/orchestration/pipeline.py` and stage modules under `runtime/orchestration/`
  - `runtime/civilization_state.py`
  - `runtime/replay_state.py`
  - `runtime/runtime_safety.py`
  - `runtime/long_run_validation.py`
- `artifact/`
  - `artifact/registry.py`, `artifact/archive.py`, `artifact/lineage.py`, `artifact/civilization_registry.py`
- `domains/`
  - `domains/domain_genome.py`, `domains/contract.py`, `domains/loader.py`, domain runtime surfaces
- `validation/`
  - `validation/system_boundary.py`, `validation/invariant.py`, `validation/artifact_law.py`, `validation/immutability.py`
- Operator path:
  - `metaos/cli.py`
  - `app/cli.py` (wrapper only)

## 4. Files / modules to demote to reference only

Demote to **reference/research tracks** (retained, not runtime-authoritative):

- `metaos_a/*`, `metaos_b/*`, `metaos_c/*`
  - Keep as conceptual A/B/C hierarchy references and experimental models.
  - Do not treat their state dataclasses as production runtime truth owners.
- `federation/*`, `ecosystem/*`
  - Keep as optional extension subsystems until full integration contract is explicit.
- `loop/model.py`, `strategy/*` (except directly imported canonical functions)
  - Keep as algorithmic helper layer with explicit adapters.

## 5. Files / modules to deprecate or remove

Deprecate/remove from active canonical path (keep shims only where needed):

1. `runtime/oed_orchestrator.py` legacy import pattern:
   - Direct imports from `metaos.archive.*` should be replaced with canonical package imports.
   - If this module remains canonical, it must not depend on missing legacy packages.
2. `runtime/soak_runner.py` legacy imports:
   - `metaos.archive.archive`, `metaos.archive.civilization_memory`, `metaos.core.supervisor` should be remapped or wrapped.
3. Duplicate boundary validator surface:
   - `validation/boundary.py` and `validation/system_boundary.py` diverge (`expansion` present only in one).
   - Mark `validation/boundary.py` deprecated or make it call `validation.system_boundary`.
4. Compatibility surfaces already marked deprecated should continue shrinking:
   - `core/*`, `kernel/*`, `evolution/*`, `metaos/kernel/*`, `metaos/runtime/*`, `metaos/domains/*`.

## 6. os_state unification plan

### 6.1 Current parallel state machines

Detected state owners / variants:

- `runtime.civilization_state.civilization_state()` (dict-based canonical aggregate)
- `runtime.replay_state.ReplayState` (event-derived replay model)
- `metaos_a.domain_state.DomainState`
- `metaos_b.manager_state.ManagerState`
- `metaos_c.civilization_state.CivilizationState`
- `genesis.state_machine.tick_phase()` (mini state transition)
- plus optional extension states:
  - `ecosystem.ecosystem_state.ecosystem_state()`
  - `federation.federation_state.federation_state()`

### 6.2 Canonical state model to keep

Keep **one authoritative OS-level state contract**:

- canonical owner: `runtime.civilization_state.civilization_state`
- replay source: `runtime.replay_state.replay_state`
- law/invariant checks: `genesis/*` and `validation/*`

Recommended naming alignment:
- define explicit alias: `os_state = civilization_state` in canonical contract docs and runtime API.

### 6.3 Migration path

1. Introduce `runtime/os_state.py` as a typed façade:
   - `read_os_state() -> dict`
   - `merge_os_state(...)`
   - `validate_os_state(...)`
2. Convert `metaos_a/b/c` state classes to adapters only:
   - `to_os_state_patch()` and `from_os_state_view()`.
3. Route all stage modules (`runtime/orchestration/*`) to consume/emit only `os_state` schema keys.
4. Keep `ReplayState` as persistence/rebuild helper, not independent control state.

## 7. Role-boundary violations and exact fixes

Required Level3 separation is currently implicit and violated by mixed responsibilities.

### 7.1 Violations

- Strategy + execution mixed in pipeline and orchestrator paths:
  - `runtime/orchestration/pipeline.py` currently computes pressure, selection, mutation, and writes artifacts in one chain.
- Gate/Risk checks are partially embedded but not isolated:
  - `runtime/orchestration/recovery_stage.py::validate_step_state`
  - `runtime/runtime_safety.py`
- Eval and Assimilation roles are not explicitly represented as independent modules/contracts.

### 7.2 Exact additive fixes (no redesign)

Create role-locked subpackages and adapters:

- `runtime/level3/decision_core.py` (strategy synthesis only)
- `runtime/level3/executor.py` (artifact/quest execution only)
- `runtime/level3/gate_risk.py` (validation + risk gating only)
- `runtime/level3/eval.py` (scoring/evaluation only)
- `runtime/level3/assimilation.py` (parameter recalibration math only)

Then patch `runtime/orchestration/pipeline.py` to call these modules in sequence, while preserving existing stages.

Add enforceable checks:

- `validation/level3_roles.py`
  - static import boundary checks per role package
  - key ownership assertions for outputs (e.g., only `eval` writes score vectors, only `assimilation` writes tuning deltas)

## 8. Runtime integration gaps

### 8.1 Broken execution path

Observed test collection failure root cause:

- `runtime/oed_orchestrator.py` imports `metaos.archive.archive` and `metaos.archive.civilization_memory`, but `metaos/archive` package is absent.
- This breaks `metaos/runtime/oed_orchestrator.py` shim transitively and all tests importing soak/orchestrator paths.

### 8.2 Duplicate/legacy wiring

- `app/cli.py` is a wrapper around `metaos.cli`, while `metaos.cli` drives `runtime.orchestrator`; this is acceptable but should be declared in architecture docs as final CLI chain.
- Release scripts include `RUNBOOK.md` in zip validation, but repository root currently lacks it (script silently skips missing at build-time but validate script expects path list).

### 8.3 Concrete integration patches for stable baseline runtime

1. Patch imports in:
   - `runtime/oed_orchestrator.py`
   - `runtime/soak_runner.py`
   - any module importing `metaos.archive.*`
   to canonical modules:
   - `artifact.archive`
   - `runtime.civilization_memory` or `artifact.civilization_registry` as appropriate.
2. Introduce compatibility shim package:
   - `metaos/archive/__init__.py`, `metaos/archive/archive.py`, `metaos/archive/civilization_memory.py`
   forwarding to canonical owners to preserve test/backward compatibility.
3. Unify boundary validator entrypoint:
   - deprecate `validation/boundary.py` or make it strict wrapper around `validation/system_boundary.py`.
4. Add runtime import smoke test in CI:
   - `python -c "import runtime.oed_orchestrator, runtime.soak_runner, metaos.cli"`.

## 9. Assimilation / KPI / Sweep / Portfolio operational upgrade plan

### 9.1 Current status

- Portfolio exists (`strategy/quest_portfolio.py`, `runtime/supervisor.py::_sync_quests`) but capped at low breadth (`max_quests=3` in generation path).
- KPI-like outputs exist (`stability_score`, `economy_balance_score`, lineage/domain/evaluation metrics), but there is no explicit KPI contract registry.
- Sweep/search logic is distributed across pressure, mutation, evolution, and exploration modules; no single sweep coordinator.
- Assimilation (mathematical recalibration) is functionally present via guardrails/tuning modules but not represented as a role-bounded subsystem.

### 9.2 Upgrade actions

1. Add `runtime/kpi_contract.py`:
   - canonical KPI schema + required fields + hard/soft ranges.
2. Add `runtime/sweep_controller.py`:
   - owns sweep windows, perturbation plans, and exploitation/exploration ratio updates.
3. Add `runtime/assimilation_math.py`:
   - consumes KPI deltas and writes bounded parameter updates only.
4. Extend `runtime/supervisor.py` portfolio planner:
   - dynamic quest portfolio size based on pressure entropy and resource headroom.
5. Add `docs/operations/PROMOTION_RULES.md` and `docs/operations/KPI_REGISTRY.md`.

## 10. External variable adaptation upgrade plan

Current gap: no explicit external-variable adapter layer despite federation/ecosystem signals.

Additive plan:

1. Add `runtime/external_signals.py`
   - normalized inputs: market, policy, infra, compliance, demand, latency/cost envelope.
2. Add `runtime/adaptation_policy.py`
   - maps external shocks to safe, bounded adjustments (budget, quest mix, domain routing).
3. Wire into `runtime/orchestration/pressure_stage.py`:
   - combine internal replay-derived pressure with external normalized vectors using bounded weights.
4. Add fallback behavior:
   - missing external feed => deterministic neutral vector; never block core loop.

## 11. Upward numeric target corrections (Genesis-based)

The current runtime defaults are conservative and suitable for smoke operation, not upper-bound exploration.

Recommended “stability upper-bound exploration” profile (bounded increase):

1. Orchestrator cadence and horizon:
   - `tick_seconds`: 0.05 -> 0.01 (faster bounded exploration)
   - `max_ticks`: 6 -> 64 (default exploration horizon)
2. Portfolio breadth:
   - `max_quests`: 3 -> adaptive [3, 9] based on pressure entropy and available workers.
3. Worker budget policy:
   - minimum effective workers floor stays >=1, but dynamic ceiling should scale with stability + replay health (e.g., up to 4x baseline).
4. Archive pressure thresholds:
   - archive warning trigger from 0.5 utilization equivalent -> dual-threshold model (warn 0.65, hard gate 0.85).
5. Diversity guard:
   - retain anti-collapse floor around concentration ~0.68, but increase proactive branch pressure onset earlier when dominance trend persists.
6. Long-run gates:
   - elevate healthy criteria from low minimal pass (>0.2 style thresholds) to stronger steady-state targets once import/runtime stability is fixed.

All increases are additive and guarded by replay, safety, and boundary validation.

## 12. Selective promotion matrix

| Module group | Promotion tier | Reason | Action |
|---|---|---|---|
| `genesis/*` | Core-Authoritative | Kernel law + replay invariants | Keep authoritative |
| `runtime/orchestration/*`, `runtime/supervisor.py`, `runtime/civilization_state.py` | Core-Authoritative | Live control and integration path | Keep + role-separate |
| `artifact/*`, `domains/*`, `validation/*` | Core-Authoritative | Ownership aligns with architecture docs | Keep |
| `metaos/cli.py`, `app/cli.py` | Core-Operational | Operator interface | Keep, document chain |
| `metaos_a/*`, `metaos_b/*`, `metaos_c/*` | Reference-Promoted | Valuable conceptual decomposition but parallel state ownership | Demote to reference adapters |
| `ecosystem/*`, `federation/*` | Reference-Conditional | Useful extension signals, partial integration | Keep optional; no core ownership |
| `core/*`, `kernel/*`, `evolution/*`, `metaos/runtime/*`, `metaos/domains/*`, `metaos/kernel/*` | Deprecated-Compatibility | Already marked deprecated/shim | Continue shrink; no new logic |

## 13. Patch roadmap (ordered)

1. **P0 Runtime unbreak**
   - Fix missing `metaos.archive.*` import path failures via canonical imports + shims.
2. **P0 State contract lock**
   - Introduce `runtime/os_state.py` contract and map all stage IO to it.
3. **P0 Role contract enforcement**
   - Add `runtime/level3/*` wrappers and `validation/level3_roles.py` checks.
4. **P1 Boundary convergence**
   - Merge/deprecate duplicate boundary validators.
5. **P1 Documentation baseline restore**
   - Add missing baseline files as canonical pointers:
     - `Genesis.md`
     - `SYSTEM_BASELINE_v1`
     - `MASTER_CONTRACT.md`
     - `ARCHITECTURE_OVERVIEW.md`
6. **P1 KPI + promotion registry**
   - Add KPI contract doc/code and promotion/deprecation manifests.
7. **P2 Upper-bound profile activation**
   - Add `--profile stability-upper-bound` runtime profile with guarded target escalations.
8. **P2 External adaptation integration**
   - Add external signal ingestion + adaptation policy and wire into pressure stage.

## 14. Risk / compliance notes

- Legal/ethical boundaries are not codified as explicit policy modules yet; current safety focuses on technical stability and collapse prevention.
- Domain-agnostic requirement is mostly preserved in core architecture, but multiple doc/examples and defaults remain code-domain centric (`code_domain` canonical default).
- Promotion should remain selective: webnovel-like domains must remain test-bed adapters, not shape core policy assumptions.
- Before numeric escalation, import/runtime integrity must be restored; otherwise higher throughput amplifies invalid state risk.

## 15. Exact next implementation sequence

1. Repair import-path breakage (`runtime/oed_orchestrator.py`, `runtime/soak_runner.py`, legacy shims).
2. Run full test suite and ensure collection succeeds.
3. Add `runtime/os_state.py` canonical schema + stage output adapters.
4. Add Level3 role wrappers + validation checks without changing existing core logic.
5. Converge boundary validators into one canonical entrypoint.
6. Add missing baseline contract docs as root-level canonical pointers.
7. Add KPI registry + promotion matrix docs/manifests.
8. Activate upward numeric profile under feature flag + run long-run validation.
9. Integrate external signal adaptation in pressure stage with neutral fallback.
10. Promote only modules passing role-boundary and replay invariants; archive remaining references.

---

## Agent-specific findings snapshot

### Agent 1 (State + Architecture + Contracts)
- Canonical state should be `runtime.civilization_state`; parallel state dataclasses in `metaos_a/b/c` must be adapters.
- Missing requested baseline docs are a contract governance gap.
- `validation/boundary.py` vs `validation/system_boundary.py` drift is a direct contract inconsistency.

### Agent 2 (Runtime + Pipeline + Integration)
- End-to-end runtime path currently blocked by missing `metaos.archive.*` package imports.
- Shim strategy exists but is not consistently applied to archive/civilization-memory layer.
- Release/packaging scripts are mostly aligned but need strict verification of expected root artifacts.

### Agent 3 (Intelligence + Optimization)
- Exploration/evolution features are broad but under-profiled for upper-bound stability exploration.
- Portfolio breadth and horizon are conservative; increase must be tied to replay/safety health.
- Add explicit assimilation math module and sweep controller to reduce hidden coupling.

### Agent 4 (Safety + Risk + Promotion)
- Safety checks exist (`runtime/runtime_safety.py`) but legal/ethical policy layer is implicit and should be formalized.
- Selective promotion should keep canonical owners strict and preserve reference tracks without runtime authority.
- Deprecation map should be codified into enforceable CI checks (import and ownership boundaries).
