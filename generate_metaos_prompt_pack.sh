#!/bin/bash

mkdir -p metaos-build-prompts
cd metaos-build-prompts

cat <<'EOT' > 00_master_prompt.txt
You are building METAOS.

Goal:
Minimal operational Open-Ended Discovery System.

Core:
loop
log
artifact
metrics
mutation
replay
guardrail
strategy_genome
quest_manager
diversity_guard

Operations:
Run-METAOS.ps1
METAOS.env
replay.ps1
healthcheck.ps1
install-runtime.ps1
start-metaos.ps1
stop-metaos.ps1
rotate-instance.ps1
.gitignore
README_OPERATIONS.md

Rules:
append-only logs
artifact immutable
replay deterministic
instance isolation
Python 3.11
events.jsonl backbone
EOT

cat <<'EOT' > 01_core_runtime.txt
Implement METAOS core runtime.

Files:
core/loop.py
runtime/orchestrator.py

Loop:
signal
→ strategy
→ artifact
→ metrics
→ mutation
→ quest
→ decision
→ log

Requirements:
infinite loop
tick configurable
error isolation
minimal dependencies
EOT

cat <<'EOT' > 02_logging_system.txt
Implement append-only logging.

File:
core/log.py

Logs:
events.jsonl
strategies.jsonl
metrics.jsonl

Fields:
timestamp
event_type
payload

Atomic append only.
Replay compatible.
EOT

cat <<'EOT' > 03_artifact_store.txt
Implement artifact store.

File:
core/artifact.py

artifact_store/
artifact_id/

Rules:
immutable
sha256 hash
metadata stored
creation logged.
EOT

cat <<'EOT' > 04_metrics_engine.txt
Implement metrics engine.

File:
core/metrics.py

Metrics:
quality
novelty
diversity
efficiency
cost

Output numeric score.
Save to metrics.jsonl.
EOT

cat <<'EOT' > 05_strategy_genome.txt
Implement strategy genome and mutation.

Files:
core/strategy_genome.py
core/mutation.py

Strategy fields:
id
domain
eval_axes
mutation_ops
budget
parent

Mutation:
perturb
swap
recombine
EOT

cat <<'EOT' > 06_diversity_economy.txt
Implement stability systems.

Files:
runtime/diversity_guard.py
runtime/economy_controller.py

Functions:
detect collapse
adjust mutation pressure
adjust exploration ratio
resource allocation
EOT

cat <<'EOT' > 07_quest_manager.txt
Implement quest manager.

File:
runtime/quest_manager.py

Lifecycle:
proposed
selected
retired

Quest = exploration objective.
Generated from signals or metrics.
EOT

cat <<'EOT' > 08_ops_scripts.txt
Implement operations scripts.

Directory:
ops/

Files:
Run-METAOS.ps1
METAOS.env
replay.ps1
healthcheck.ps1
install-runtime.ps1
start-metaos.ps1
stop-metaos.ps1
rotate-instance.ps1
.gitignore
README_OPERATIONS.md

Run-METAOS.ps1 commands:
start
stop
health
replay
rotate
EOT

cd ..
zip -r metaos-build-prompts.zip metaos-build-prompts

echo "DONE: metaos-build-prompts.zip created"
