# Consumer Interventions

Automatic operating interventions should be derived from the consumer operating report.

Current intervention triggers:

- high escalate rate -> pause new rollouts
- migration queue present -> drain migration queue
- high hold rate -> inspect consumer
- high reject rate -> sandbox consumer
- high per-consumer escalate rate -> require human review

Operational apply path:

- `consumer-interventions` reports recommended actions without mutating runtime state
- `consumer-apply-interventions` records append-only `consumer_intervention` rows for each applied action
- soak suites may run stress iterations first, then apply the recommended actions against the accumulated report

Closed-loop control:

- intervention rows are replayed into consumer control state
- `pause_new_rollouts` changes the global rollout state to `paused`
- `inspect_consumer` changes a consumer state to `inspection_pending`
- `sandbox_consumer` changes a consumer state to `sandboxed`
- `require_human_review` changes a consumer state to `human_review_required`
- later conformance runs must respect this control state before adapter evaluation continues
- blocked runs must also project queue and supervisor state as `paused` or `blocked`, not just return a top-level verdict
