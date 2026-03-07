# Architecture Contradictions

## Resolved

1. `runtime/orchestrator.py` mixed legacy `run` profile logic with newer runtime profiles and contained duplicate branches.
2. `runtime/long_run_validation.py` contained multiple overlapping implementations, undefined variables, and incompatible return shapes.
3. `validation/constitution.py` and `validation/system_boundary.py` were syntactically broken and therefore incapable of enforcing Genesis faithfully.
4. `ops/validate-runtime.sh` invoked `long-run-check` with an unsupported `--profile` flag and ignored failure.

## Remaining Compatibility Tension

1. The repo still carries shim trees in `core/`, `kernel/`, `evolution/`, and `metaos/runtime/`.
2. `README.md`, root `RUNBOOK.md`, and some historical docs still reference both `civilization` and `production` naming.
3. Long-horizon metrics remain derived from current runtime summaries rather than a fully separate replay digest protocol.

## Decision

- Canonical runtime operation is profile-driven with `smoke`, `bootstrap`, `aggressive`, `soak`, and `production`.
- `civilization` and `run` remain compatibility aliases for the unbounded production profile.
- Tier-based long-run validation remains available for operator workflows and release checks.
