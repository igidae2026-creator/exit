# Invariant Traceability Matrix

GENESIS invariants mapped to implementation and tests.

| Invariant | Runtime/Code owner | Validation owner | Test coverage | Operator surface |
|---|---|---|---|---|
| perpetual exploration loop law | `runtime/core_loop.py`, `runtime/orchestrator.py` | `validation/gates.py`, `validation/genesis_invariants.py` | `tests/test_genesis_invariant_validation.py` | `metaos validate`, `metaos run` |
| signal->generate->evaluate->select->mutate->archive->repeat | `runtime/core_loop.py`, `runtime/oed_orchestrator.py` | `validation/constitution.py` | `tests/test_genesis_invariant_validation.py` | `metaos validate` |
| append-only truth | `genesis/`, `runtime/replay_state.py` | `validation/genesis_invariants.py` | `tests/test_kernel_replay.py`, `tests/test_genesis_invariant_validation.py` | `metaos replay-check` |
| replayable state | `runtime/replay_state.py`, `runtime/orchestrator.py` | `validation/genesis_invariants.py` | `tests/test_kernel_replay.py` | `metaos replay`, `metaos replay-check` |
| artifact immutability | `artifact/*` | `validation/artifact_law.py`, `validation/genesis_invariants.py` | `tests/test_artifact_lineage_arch.py` | `metaos validate` |
| minimal core + domain autonomy | `genesis/`, `domains/loader.py` | `validation/system_boundary.py`, `validation/genesis_invariants.py` | `tests/test_domain_autonomy.py`, `tests/test_boundary_enforcement.py` | `metaos validate` |
| lineage diversity preservation | `runtime/lineage_ecology.py`, `runtime/diversity_guard.py` | `validation/genesis_invariants.py` | `tests/test_lineage_ecology.py` | `metaos lineage-status` |
| failure protocol (plateau/collapse/repair/replay restore) | `runtime/collapse_guard.py`, `runtime/repair_system.py`, `runtime/replay_state.py` | `validation/genesis_invariants.py` | `tests/test_failure_protocol.py` | `metaos stability-status`, `metaos safety-status` |

## Runtime mode separation
- Production perpetual mode: no `max_ticks`, no stop gate.
- Dev/test bounded mode: positive `max_ticks`, explicit stop gate.
- Enforced by `validation.gates.validate_runtime_gates` and exposed via CLI `validate`.
