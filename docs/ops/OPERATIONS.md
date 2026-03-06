# Operations

- Start METAOS: `bash ops/run-metaos.sh`
- Stop safely: terminate the process between ticks or use supervisor safe shutdown
- Inspect runtime health: `bash ops/healthcheck.sh`
- Inspect lineage survival: `python -m app.cli lineage-status`
- Inspect domain growth: `python -m app.cli domain-status`
