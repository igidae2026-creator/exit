# Audit Manifest

## Scope

Recursive audit completed across:

- `app/`, `artifact/`, `core/`, `docs/`, `domains/`, `ecosystem/`, `evolution/`, `federation/`
- `genesis/`, `kernel/`, `loop/`, `metaos-build-prompts/`, `metaos/`, `metaos_a/`, `metaos_b/`, `metaos_c/`
- `observer/`, `ops/`, `runtime/`, `scripts/`, `signal/`, `strategy/`, `tests/`, `validation/`
- Root files including `README.md`, `RUNBOOK.md`, `pyproject.toml`, `setup.py`, `run_metaos.py`, `run-phase6-soak.py`, `run-oed-smoke.sh`, `generate_metaos_prompt_pack.sh`, `py_compile.py`, `.gitignore`

## Verified Starting Signals

- `README.md` already declared canonical ownership and profile-driven operation.
- `app/cli.py` is a thin forwarder to `metaos.cli`.
- `pyproject.toml` packaged the required top-level modules, but profile/runtime truth was not coherent.
- `runtime/orchestrator.py` and `runtime/long_run_validation.py` contained duplicate and syntactically broken implementations.
- `validation/constitution.py` and `validation/system_boundary.py` were malformed and under-enforced.
- `ops/validate-runtime.sh` masked long-run failure with `|| true` and used stale CLI arguments.
- Required audit/report files were missing.

## Test Inventory Categories

- Smoke and CLI: `tests/test_cli_smoke.py`, `tests/test_cli_commands.py`, `tests/test_oed_smoke.py`
- Structural and ownership: `tests/test_packaging_truth.py`, `tests/test_packaging_roots.py`, `tests/test_ownership_manifest.py`
- Invariant and boundary: `tests/test_boundary_constitution.py`, `tests/test_boundary_enforcement.py`, `tests/test_genesis_invariant_validation.py`, `tests/test_artifact_law.py`
- Replay and append-only: `tests/test_replay_determinism.py`, `tests/test_replay_state_hash.py`, `tests/test_kernel_replay.py`
- Long-run and soak: `tests/test_long_run_tiers.py`, `tests/test_long_run_ops.py`, `tests/test_soak_runner.py`, `tests/test_soak_long.py`
- Ecology and lineage: `tests/test_lineage_ecology.py`, `tests/test_multi_lineage_survival.py`, `tests/test_long_run_multi_lineage.py`
- Domain autonomy: `tests/test_domain_autonomy.py`, `tests/test_domain_lifecycle.py`, `tests/test_domain_discovery.py`
- Federation and ecosystem: `tests/test_federation_safety.py`, `tests/test_federation_replay.py`, `tests/test_artifact_market.py`
- Release and docs truth: `tests/test_release_install.py`, `tests/test_release_tree.py`, `tests/test_docs_truth_sync.py`, `tests/test_docs_completeness.py`

## Primary Contradictions Found

- Runtime bounded/unbounded semantics diverged between CLI, orchestrator, docs, and ops.
- Long-run validation mixed tier-based and profile-based code paths into one broken module.
- Boundary law and constitution law did not reliably enforce Genesis roles and pressure axes.
- Release validation checked tree shape but not mandatory audit/remediation truth artifacts.
