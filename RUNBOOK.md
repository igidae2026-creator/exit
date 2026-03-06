# METAOS Civilization MVP Runbook

Run from the repo root:

```bash
python -m metaos.cli run-once --ticks 1
```

Expected outputs:

- `data/events.jsonl` grows with supervisor, quest, policy, quota, archive, and cycle events.
- `data/artifact_registry.jsonl` grows with append-only artifact lineage records.
- `data/metrics.jsonl` grows with evaluation metrics.
- `artifact_store/<artifact_id>/artifact.json` appears for quest, policy, strategy, evaluation, output, and repair artifacts as needed.
- The command prints one JSON summary for the last completed cycle.

Validation command:

```bash
python -m metaos.cli validate
```

Replay command:

```bash
python -m metaos.cli replay
```
