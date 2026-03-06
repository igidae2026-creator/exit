# GENESIS

Enforce GENESIS specification across the METAOS codebase.

Do not explain.
Patch in place.
Do not break existing tests.
Architecture correctness takes priority.

GENESIS REQUIREMENTS

Purpose:
Create a system that continuously explores and evolves solutions under invariant constraints.

Core Loop:
signal → generate → evaluate → select → mutate → archive → repeat
This loop must never stop.

Human Authority:
Human defines only:
goal
essence
constraints
acceptance

System performs:
exploration
implementation
validation
evolution

INVARIANTS (must never be violated)

append-only truth
replayable state
artifact immutability
minimal core
domain autonomy

IMPLEMENTATION TASKS

1. Enforce canonical exploration loop

Create:
runtime/exploration_loop.py

Function:
run_loop(signal_source)

Pipeline:
signal
generate
evaluate
select
mutate
archive
repeat

Ensure no code path can terminate the loop except supervisor safe shutdown.

2. Canonical truth spine

Ensure all runtime state derives only from append-only logs.

Required truth logs:

events.jsonl
metrics.jsonl
artifact_registry.jsonl

Create/verify:

kernel/spine.py
kernel/replay.py

Function:
replay_state()

Replay must deterministically rebuild runtime state.

3. Artifact law enforcement

Create:

validation/artifact_law.py

Rules:

artifact must be immutable
artifact must contain:
artifact_id
artifact_type
parent_ids
payload
score_vector
created_at

All artifact writes must pass through artifact/store.py.

4. Exploration pressure system

Ensure canonical pressures exist:

novelty_pressure
diversity_pressure
efficiency_pressure
repair_pressure
domain_shift_pressure
reframing_pressure

Create/verify:

runtime/pressure_model.py

Pressure must influence:

mutation bias
selection bias
resource allocation
quest generation

5. Policy evolution runtime

Policies must evolve as artifacts.

Create:

runtime/policy_runtime.py

Rules:

policies are artifacts
policies may swap at tick boundaries
no system restart required

6. Resource allocation

Create/verify:

runtime/resource_allocator.py

Inputs:

pressure
ecology
population

Outputs:

attention_budget
mutation_budget
selection_weights
runtime_slots

7. Lineage ecology

Create:

runtime/lineage_ecology.py

Responsibilities:

track lineage survival
prevent single-lineage dominance
maintain diversity floor

8. Knowledge accumulation

Create:

runtime/knowledge_system.py

Use:

artifact archives
lineage graphs
civilization memory

Future exploration must reference accumulated artifacts.

9. Domain autonomy

Enforce domain contract:

domains/contract.py

Required methods:

input()
generate()
evaluate()
metrics()
loop()

Kernel must never contain domain logic.

10. Failure protocol

Update:

kernel/supervisor.py

Rules:

plateau → exploration
collapse → diversity pressure
repair failure → repair escalation
invalid state → replay restore

11. Acceptance tests

Add tests:

tests/test_genesis_loop.py
tests/test_artifact_law.py
tests/test_pressure_model.py
tests/test_policy_evolution.py
tests/test_resource_allocation.py
tests/test_lineage_ecology.py
tests/test_replay_determinism.py
tests/test_domain_autonomy.py
tests/test_failure_protocol.py
