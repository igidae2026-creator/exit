# Release

Release truth must match code truth.

Canonical packages:
- `genesis/`
- `metaos_a/`
- `metaos_b/`
- `metaos_c/`
- `runtime/`
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

Long-horizon release gates:
- `stability_score` and `economy_balance_score` must be present in validation output
- domain lifecycle must report active, inactive, and retired sets explicitly
- guardrail interventions must remain bounded and replay-derived
