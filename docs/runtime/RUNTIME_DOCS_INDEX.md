# Runtime Docs Index: Read Order For AI Agents

Use this read order when deciding what MetaOS runtime work means and what should be changed next.

## 1. Identity And Success Criteria

- `PLATFORM_LAYER_FRAMING.md`
- `HUMAN_INTERVENTION_THRESHOLD.md`
- `CURRENT_PLATFORM_STATUS.md`

Read these first when the question is:

- what layer are we working in
- what is the real success threshold
- what should not drift

## 2. Runtime Core And Consumer Contracts

- `ADAPTER_RUNTIME_CORE.md`
- `CONSUMER_VERSIONING.md`
- `CONSUMER_ONBOARDING_TEMPLATE.md`

Read these when the question is:

- how a consumer connects to MetaOS
- what compatibility rules apply
- whether a new consumer should require core edits

## 3. Operating Control And Calibration

- `CONSUMER_OPERATING_REPORT.md`
- `CONSUMER_INTERVENTIONS.md`
- `NEXT_OPERATING_PRIORITY.md`

Read these when the question is:

- how runtime health is measured
- when reports turn into control-state changes
- what boundary stress and soak work should happen next

## 4. Lower-Level Runtime Specifications

- `FAILURE_PROTOCOL.md`
- `RUNTIME_FAILURE_HANDLING.md`
- `SUPERVISOR_SPEC.md`
- `REPLAY_STATE_SPEC.md`
- `STATE_DERIVATION_SPEC.md`
- `STATE_MODEL.md`
- `POLICY_RUNTIME.md`
- `QUOTA_ALLOCATOR_SPEC.md`

Read these only when the task is about deeper execution, replay, failure, or state law.
