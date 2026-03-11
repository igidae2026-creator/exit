# AUTONOMY_TARGET

## Purpose

This document isolates the autonomy and quality bar for the repository.
It defines the unattended execution standard separately from broader ownership and integration rules.

## Target Standard

- The target is a 24-hour autonomous loop that keeps producing high-quality outputs with minimal human micromanagement.
- Human involvement is allowed, but it must not be required for routine continuation.
- The desired steady state is that human intervention adds little or no meaningful quality gain over the system's default output.
- Human involvement should progressively shift from active production to approval, audit, and rare correction.
- Automation limited only to already-included scope is not enough; the outer loop must also evaluate newly arriving material, decide whether it belongs in scope, and promote it automatically when it clears quality and relevance gates.
- The system should continuously raise, reject, defer, or promote work items and source material without waiting for manual triage.

## Evaluation Gate

- If the system still depends on frequent operator steering to maintain runtime or policy quality, the target has not yet been met.
- Release, validation, replay, artifact, and runtime decisions should be judged by unattended operation without quality collapse.
- Quality gates should prefer append-only truth preservation, deterministic replay, low review noise, and no canonical drift under rerun.
- If newly ingested material still needs a person to decide routine scope selection, prioritization, or promotion into the active loop, the target has not yet been met.

## Operational Implications

- Persist intent, progress, and resume state in repository files instead of relying on chat memory.
- Prefer resumable loops, manifests, ledgers, append-only records, and structured validation artifacts over conversational continuation.
- Treat automation changes as suspect if they increase dependence on manual steering.
- Favor replayable policy and runtime evolution over one-off operator-guided correction.
- Add an outer ingestion and triage layer that can classify new inputs, bind them to the right subsystem, and either reject, sandbox, or promote them without operator involvement.
- Judge autonomy progress against the stricter bar of "human intervention produces negligible additional quality gain," not merely "the existing loop runs unattended."

## Core Control Architecture

- Do not jump directly from a supervisor loop plus state file plus background execution into full autonomy claims.
- Treat the following four primitives as the core execution substrate: append-only event log, typed snapshots, job queue, and supervisor.
- The event log should be the durable chronological truth for actions, decisions, failures, promotions, and repairs.
- Typed snapshots should capture validated state boundaries that can be restored, compared, replayed, and audited without ambiguity.
- The job queue should own pending work, retries, priority changes, deferrals, and promotion flow instead of burying them in ad hoc loop state.
- The supervisor should coordinate execution, safety response, quota control, recovery, and escalation over those primitives rather than acting as a monolithic hidden controller.
- Policy should sit above that substrate as an explicit layer that evaluates events, snapshots, and queued work, then decides routing, admission, promotion, rejection, or safe-mode constraints.
- New autonomy work should be judged partly by whether it strengthens this layered model instead of bypassing it with opaque background scripts or state-file-only orchestration.
