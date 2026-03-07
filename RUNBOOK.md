# METAOS Runbook

Canonical control flow:
- `civilization_state`
- `-> pressure`
- `-> allocation`
- `-> questing`
- `-> artifact evolution`
- `-> domain evolution`
- `-> memory accumulation`


Boundary truth map:
- `docs/architecture/BOUNDARY_TRUTH_MAP.md`

Invariant traceability:
- `docs/architecture/INVARIANT_TRACEABILITY.md`

Hierarchy:
- `GENESIS -> METAOS-A -> METAOS-B -> METAOS-C`

Operator actions:
- start runtime: `bash ops/run-metaos.sh`
- check health: `bash ops/healthcheck.sh`
- validate replay and runtime status: `bash ops/validate-runtime.sh`
- inspect civilization state: `python -m app.cli civilization-status`
- inspect lineage status: `python -m app.cli lineage-status`
- inspect domain status: `python -m app.cli domain-status`
- inspect economy status: `python -m app.cli economy-status`
- inspect stability status: `python -m app.cli stability-status`
- inspect safety status: `python -m app.cli safety-status`
- run long-run validation: `python -m app.cli long-run-check`
- rotate runtime safely: `bash ops/rotate-runtime.sh`
- clean transient runtime state: `bash ops/cleanup-runtime.sh`

Automatic actions:
- exploration and reframing
- artifact mutation and selection
- domain discovery within bounded expansion policy
- domain retirement and bounded resurrection
- civilization memory accumulation
- replay-compatible continuation
