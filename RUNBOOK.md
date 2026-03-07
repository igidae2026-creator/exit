# METAOS Runbook

This runbook covers the installed CLI, source release validation, replay restore, and operator escalation boundaries.

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

Profiles:
- `smoke`: fast validation and replay proof
- `bootstrap`: bounded startup ecology check
- `aggressive`: stronger bounded local validation
- `soak`: long-run stability checks
- `endurance`: large-budget and long-history stress
- `production`: unbounded canonical runtime
- `civilization`: compatibility alias for `production`

Operator actions:
- install surface: `metaos --help`
- start runtime: `bash ops/run-metaos.sh`
- check health: `bash ops/healthcheck.sh`
- validate replay and runtime status: `bash ops/validate-runtime.sh`
- inspect health from installed CLI: `metaos health`
- inspect replay from installed CLI: `metaos replay-check`
- inspect civilization state: `python -m app.cli civilization-status`
- inspect lineage status: `python -m app.cli lineage-status`
- inspect domain status: `python -m app.cli domain-status`
- inspect economy status: `python -m app.cli economy-status`
- inspect stability status: `python -m app.cli stability-status`
- inspect safety status: `python -m app.cli safety-status`
- run long-run validation: `python -m app.cli long-run-check --tier smoke`
- run bootstrap validation: `python -m app.cli long-run-check --tier bootstrap`
- run bounded validation: `python -m app.cli long-run-check --tier bounded`
- run aggressive validation: `python -m app.cli long-run-check --tier aggressive`
- run soak validation: `python -m app.cli long-run-check --tier soak`
- rotate runtime safely: `bash ops/rotate-runtime.sh`
- clean transient runtime state: `bash ops/cleanup-runtime.sh`

Automatic actions:
- exploration and reframing
- artifact mutation and selection
- domain discovery within bounded expansion policy
- domain retirement and bounded resurrection
- civilization memory accumulation
- replay-compatible continuation

Failure protocol:
- plateau -> exploration pressure
- collapse -> diversity repair
- repair failure -> repair escalation
- invalid state -> replay restore

Escalate manually when:
- `metaos replay-check` fails
- `metaos safety-status` reports repeated `repair_escalation`, `foreign_monoculture`, or `mirror_storm`
- `metaos long-run-check` returns `healthy=false`
- `bash ops/validate-runtime.sh` shows replay divergence or invalid state restore failure
