# Release

Release truth must match code truth.

## Single source of truth

- `release_manifest.json` is the canonical release and ownership manifest.
- `scripts/build_release_zip.sh` and `scripts/validate_release_tree.sh` both load `scripts/release_manifest.py` so build/validation stay synchronized.

## Canonical packaged surfaces

- `metaos/` (public CLI owner)
- `app/` (compatibility shim CLI)
- `artifact/`
- `domains/`
- `federation/`
- `genesis/`
- `loop/`
- `metaos_a/`
- `metaos_b/`
- `metaos_c/`
- `observer/`
- `runtime/`
- `signal/`
- `strategy/`
- `validation/`

## Compatibility-only surfaces

- `core/`
- `kernel/`
- `evolution/`
- `metaos/kernel/`
- `metaos/runtime/`
- `metaos/domains/`

## Release commands

- `python -m app.cli build-release`
- `python -m app.cli validate-release`
- `python -m app.cli long-run-check`
- `bash ops/validate-runtime.sh`

## Long-horizon release gates

- `stability_score` and `economy_balance_score` must be present in validation output.
- Domain lifecycle must report active, inactive, and retired sets explicitly.
- Guardrail interventions must remain bounded and replay-derived.
