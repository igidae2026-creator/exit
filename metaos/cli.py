from __future__ import annotations

import argparse
import json
from typing import Sequence

from runtime.orchestrator import Orchestrator, OrchestratorConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="metaos", description="METAOS civilization runtime CLI")
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--artifact-dir", default=None)
    parser.add_argument("--state-dir", default=None)
    parser.add_argument("--archive-dir", default=None)
    parser.add_argument("--domain", default="code_domain")
    parser.add_argument("--tick-seconds", type=float, default=None)
    parser.add_argument("--max-ticks", type=int, default=None)

    subparsers = parser.add_subparsers(dest="command", required=False)

    validate_parser = subparsers.add_parser("validate", help="Validate runtime wiring and invariants")
    validate_parser.set_defaults(func=cmd_validate)

    run_once_parser = subparsers.add_parser("run-once", help="Run one or more civilization ticks")
    run_once_parser.add_argument("--ticks", type=int, default=1)
    run_once_parser.set_defaults(func=cmd_run_once)

    replay_parser = subparsers.add_parser("replay", help="Replay append-only runtime state")
    replay_parser.set_defaults(func=cmd_replay)

    status_parser = subparsers.add_parser("status", help="Inspect runtime status")
    status_parser.set_defaults(func=cmd_status)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect runtime status")
    inspect_parser.set_defaults(func=cmd_status)
    return parser


def build_runtime(args: argparse.Namespace) -> Orchestrator:
    config = OrchestratorConfig.from_env()
    if args.data_dir:
        config.data_dir = type(config.data_dir)(args.data_dir)
    if args.artifact_dir:
        config.artifact_store_dir = type(config.artifact_store_dir)(args.artifact_dir)
    if args.state_dir:
        config.state_dir = type(config.state_dir)(args.state_dir)
    if args.archive_dir:
        config.archive_dir = type(config.archive_dir)(args.archive_dir)
    if args.domain:
        config.canonical_domain = args.domain
    if args.tick_seconds is not None:
        config.tick_seconds = args.tick_seconds
    if args.max_ticks is not None:
        config.max_ticks = args.max_ticks
    return Orchestrator(config)


def cmd_validate(args: argparse.Namespace) -> int:
    runtime = build_runtime(args)
    summary = runtime.validate()
    print(json.dumps(summary, ensure_ascii=True))
    return 0


def cmd_run_once(args: argparse.Namespace) -> int:
    runtime = build_runtime(args)
    reports = runtime.run(max_ticks=max(1, int(args.ticks)))
    print(json.dumps(reports[-1], ensure_ascii=True))
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    runtime = build_runtime(args)
    print(json.dumps(runtime.replay(), ensure_ascii=True))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    runtime = build_runtime(args)
    summary = runtime.replay()
    summary["validate"] = runtime.validate()["ok"]
    print(json.dumps(summary, ensure_ascii=True))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
