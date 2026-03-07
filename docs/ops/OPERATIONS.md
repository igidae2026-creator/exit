# Operations

Runtime ownership lives in `runtime/`. CLI and observer surfaces are read-only operator interfaces.

Operator surfaces:
- `bash ops/run-metaos.sh`
- `bash ops/healthcheck.sh`
- `bash ops/validate-runtime.sh`
- `python -m app.cli civilization-status`
- `python -m app.cli lineage-status`
- `python -m app.cli domain-status`
- `python -m app.cli economy-status`
- `python -m app.cli stability-status`
- `python -m app.cli safety-status`
- `python -m app.cli replay-check`
- `python -m app.cli long-run-check`

Observed status:
- `civilization_state` is the primary control summary
- healthy operation means bounded exploration, bounded churn, live replay continuity, and explicit guardrail actions when pressure drifts
- domain reporting distinguishes `created_domains`, `active_domains`, `inactive_domains`, `retired_domains`, and `resurrectable_domains`
- `active_domain_distribution` is the active-share view
- lineage health distinguishes coexistence, dominance lock-in, dormancy, and zombie lineages
- economy balance tracks budget skew, not just total budget volume
