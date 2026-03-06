# METAOS Operations

Operational scripts for lifecycle management, health checks, replay, and instance rotation.

## Files

- `Run-METAOS.ps1`: command router for common operations.
- `METAOS.env`: environment configuration.
- `install-runtime.ps1`: Python/runtime validation and optional dependency install.
- `start-metaos.ps1`: starts METAOS runtime and writes PID/health state.
- `stop-metaos.ps1`: stops runtime using PID file.
- `healthcheck.ps1`: reports runtime and event-log status.
- `replay.ps1`: reads and replays the latest events from `events.jsonl`.
- `rotate-instance.ps1`: archives current instance directory and optionally restarts.

## Quick Start

From the repository root:

```powershell
pwsh ./ops/Run-METAOS.ps1 start
pwsh ./ops/Run-METAOS.ps1 health
pwsh ./ops/Run-METAOS.ps1 replay
pwsh ./ops/Run-METAOS.ps1 rotate
pwsh ./ops/Run-METAOS.ps1 stop
```

## Command Reference

`Run-METAOS.ps1` supports:

- `start`
- `stop`
- `health`
- `replay`
- `rotate`

Pass through additional options to underlying scripts:

```powershell
pwsh ./ops/Run-METAOS.ps1 start -- -Instance prod -InstallRuntime
pwsh ./ops/Run-METAOS.ps1 health -- -Instance prod -Json
pwsh ./ops/Run-METAOS.ps1 replay -- -Instance prod -Limit 200 -AsJson
pwsh ./ops/Run-METAOS.ps1 rotate -- -Instance prod -NoRestart
```

## Runtime Layout

By default, runtime state is created under `instances/<instance-id>/`:

- `metaos.pid`: active process id
- `health.json`: latest lifecycle status
- `events.jsonl`: append-only event stream
- `logs/stdout.log`
- `logs/stderr.log`

Archived instances are moved to `instances/_archive/<instance-id>-<timestamp>/` during rotate.

## Configuration

Edit `ops/METAOS.env`:

- `METAOS_ROOT`: repo root relative to `ops/` (default `..`)
- `METAOS_INSTANCE_ID`: default instance id
- `METAOS_INSTANCES_DIR`: runtime state directory
- `METAOS_ENTRYPOINT`: python entrypoint file
- `METAOS_PYTHON`: python command
- `METAOS_RUNTIME_ARGS`: optional args appended at startup
- `METAOS_STOP_TIMEOUT_SEC`: graceful stop timeout
- `METAOS_REPLAY_LIMIT`: default replay tail size

## Notes

- Scripts are designed for PowerShell 7 (`pwsh`) and also work in Windows PowerShell for core flows.
- `healthcheck.ps1` exits with code `0` when running, `1` when not running.
