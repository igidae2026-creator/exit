# Stability Checklist

Binary pre-release gates.

## 1. Core Stability
- [ ] Runtime command surface responds: `run`, `run-once`, `validate`, `replay`, `status`, `health`.
- [ ] Canonical ownership remains in `genesis/`, `runtime/`, `artifact/`, `domains/`, `validation/`, `metaos_a/`, `metaos_b/`, `metaos_c/`.
- [ ] Compatibility-only surfaces remain shims and do not become owners.

## 2. Replay Stability
- [ ] Replay reconstruction succeeds on smoke/stability/endurance horizons.
- [ ] Replay divergence is zero in release validation outputs.
- [ ] Recovery from invalid state restores safe progress within bounded ticks.

## 3. Artifact Stability
- [ ] New runtime artifacts are immutable and lineage-linked.
- [ ] No silent mutation of source-of-truth registries.
- [ ] Derived state can be reconstructed from append-only logs + artifacts only.

## 4. Evolution Stability
- [ ] Policy generations and evaluation generations both grow materially.
- [ ] Runtime can replace policies without rebooting core process.
- [ ] Diversity repair triggers before monoculture lock-in.

## 5. Runtime Stability
- [ ] Domain expansion defaults permit multi-domain growth in normal pressure.
- [ ] Dominance index remains within configured healthy bounds outside crisis mode.
- [ ] Guardrail actions are observable and auditable.

## 6. Civilization Stability
- [ ] Surviving lineages and active domains meet profile floors.
- [ ] Pressure/economy/stability surfaces agree with replay-derived state.
- [ ] Operator runbook steps are executable end-to-end.
