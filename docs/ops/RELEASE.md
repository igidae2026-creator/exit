# Release

Release truth must match code truth.

Canonical packages:
- `app/`
- `genesis/`
- `ecosystem/`
- `federation/`
- `metaos_a/`
- `metaos_b/`
- `metaos_c/`
- `observer/`
- `runtime/`
- `signal/`
- `strategy/`
- `loop/`
- `artifact/`
- `domains/`
- `validation/`

Compatibility-only surfaces:
- `core/`
- `kernel/`
- `evolution/`
- `metaos/kernel/`
- `metaos/runtime/`
- `metaos/domains/`

Release commands:
- `python -m app.cli build-release`
- `python -m app.cli validate-release`
- `python -m app.cli long-run-check`
- `bash ops/validate-runtime.sh`

Manifest truth:
- `pyproject.toml` defines installed package discovery
- `validation/ownership_manifest.json` defines released source contents and ownership classification
- `scripts/build_release_zip.sh` and `scripts/validate_release_tree.sh` consume the same manifest
- `tests/test_release_install.py` validates clean-room wheel install and CLI execution

Long-horizon release gates:
- `stability_score` and `economy_balance_score` must be present in validation output
- domain lifecycle must report active, inactive, and retired sets explicitly
- guardrail interventions must remain bounded and replay-derived
