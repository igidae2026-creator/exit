# METAOS Master Specification

METAOS operates through an exploration loop.

signal → strategy → artifact → metrics → mutation → next strategy

Signals introduce exploration opportunities.

Sources include:

external environment  
human input  
system feedback  
random exploration  

Strategies transform signals into exploration programs.

Artifacts are immutable outputs of exploration.

Metrics evaluate artifact outcomes.

Mutation generates new strategies.

All actions generate events stored in events.jsonl.

State is derived by replaying events.
