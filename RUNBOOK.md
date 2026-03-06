# METAOS Open-Ended Discovery MVP Runbook

Run from the repo root:

```bash
python run_metaos.py
```

Expected outputs:

- autonomous exploration loop remains active until interrupted
- `data/events.jsonl` grows with supervisor, quest, policy, quota, archive, and cycle events.
- `data/artifact_registry.jsonl` grows with append-only artifact lineage records.
- `data/metrics.jsonl` grows with evaluation metrics.
- `artifact_store/<artifact_id>/artifact.json` appears for quest, policy, strategy, evaluation, output, and repair artifacts as needed.
- `archive/` stores retained artifact, policy, quest, repair, genome, pressure, and quota snapshots.
- the command prints one report per completed cycle.

Validation command:

```bash
python -m metaos.cli validate
```

Replay command:

```bash
python -m metaos.cli replay
```

Log locations:

- `data/events.jsonl`
- `data/artifact_registry.jsonl`
- `data/metrics.jsonl`

Basic troubleshooting:

- if startup aborts immediately, verify `docs/METAOS_CONSTITUTION.md` and `docs/METAOS_MASTER_SPEC.md` were not modified
- if you need a bounded smoke run, use `METAOS_MAX_TICKS=1 python run_metaos.py`
- if replay looks stale, run `python -m metaos.cli replay`


## CONSTITUTION IMMUTABILITY

The following files are immutable and MUST NEVER be modified, overwritten, appended to, renamed, or deleted:

- docs/core/METAOS_CONSTITUTION.md
- docs/core/METAOS_MASTER_SPEC.md

These files must remain byte-for-byte identical to the imported source from METAOS_FINAL_DOCS.zip.
Any attempted change is prohibited and must be blocked by hooks, guards, and policy.
