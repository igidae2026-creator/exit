# Recovery

- Invalid state -> replay restore: `python -m app.cli replay-check`
- Truth verification: inspect `events.jsonl`, `metrics.jsonl`, `artifact_registry.jsonl`
- Archive recovery: restore from `archive/` and rotation manifest
- Restart procedure: rerun `bash ops/run-metaos.sh`
- Safe mode: `METAOS_SOAK_FAST=1 bash ops/run-metaos.sh`
