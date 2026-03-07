# METAOS Runbook

Canonical control flow:
- `civilization_state`
- `-> pressure`
- `-> allocation`
- `-> questing`
- `-> artifact evolution`
- `-> domain evolution`
- `-> memory accumulation`

Hierarchy:
- `GENESIS -> METAOS-A -> METAOS-B -> METAOS-C`

Profiles:
- `smoke`: fast validation and replay proof (`--profile smoke`)
- `soak`: long-run stability checks (`--profile soak`)
- `endurance`: large-budget/large-history stress (`--profile endurance`)
- `civilization`: unbounded canonical runtime (`--profile civilization`, no `--max-ticks`)

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
- run long-run validation: `python -m app.cli long-run-check --profile smoke`
- rotate runtime safely: `bash ops/rotate-runtime.sh`
- clean transient runtime state: `bash ops/cleanup-runtime.sh`

Failure protocol:
- plateau -> exploration pressure
- collapse -> diversity repair
- repair failure -> repair escalation
- invalid state -> replay restore
