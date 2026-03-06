# METAOS Constitution

METAOS is a Personal Autonomous Exploration Operating System.

METAOS exists to explore possibility space.

Ceilings are not set.
They are discovered through exploration.

METAOS is exploration-driven, not goal-driven.

Human role:

Architect  
Observer  
Signal Source  

Human control is optional.

Core loop:

signal → strategy → artifact → metrics → mutation → next strategy

Artifacts are immutable.

Logs are append-only.

Primary logs:

events.jsonl  
signals.jsonl  
strategies.jsonl  
artifact_registry.jsonl  
metrics.jsonl  
decisions.jsonl  

State is derived through event replay.

Instances never share state or strategy.

Only insights may be exchanged between instances.

Supervisor coordinates instances without modifying artifacts or logs.
