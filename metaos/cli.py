from __future__ import annotations

import argparse
import json
import subprocess
from typing import Sequence

from observer.projections import civilization_projection, domain_projection, economy_projection, lineage_projection, pressure_projection, replay_projection, safety_projection, stability_projection, status_projection
from runtime.orchestrator import Orchestrator, OrchestratorConfig
from runtime.long_run_validation import LONG_RUN_TIERS, validate_long_run
from validation.system_boundary import validate_system_boundary


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

    run_parser = subparsers.add_parser("run", help="Run METAOS")
    run_parser.add_argument("--ticks", type=int, default=None)
    run_parser.set_defaults(func=cmd_run)

    validate_parser = subparsers.add_parser("validate", help="Validate runtime wiring and invariants")
    validate_parser.set_defaults(func=cmd_validate)

    run_once_parser = subparsers.add_parser("run-once", help="Run one or more civilization ticks")
    run_once_parser.add_argument("--ticks", type=int, default=1)
    run_once_parser.set_defaults(func=cmd_run_once)

    replay_parser = subparsers.add_parser("replay", help="Replay append-only runtime state")
    replay_parser.set_defaults(func=cmd_replay)

    replay_check_parser = subparsers.add_parser("replay-check", help="Replay append-only runtime state and verify it is readable")
    replay_check_parser.set_defaults(func=cmd_replay_check)

    status_parser = subparsers.add_parser("status", help="Inspect runtime status")
    status_parser.set_defaults(func=cmd_status)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect runtime status")
    inspect_parser.set_defaults(func=cmd_status)

    health_parser = subparsers.add_parser("health", help="Inspect runtime health")
    health_parser.set_defaults(func=cmd_health)

    civilization_parser = subparsers.add_parser("civilization-status", help="Inspect civilization state")
    civilization_parser.set_defaults(func=cmd_civilization_status)

    lineage_parser = subparsers.add_parser("lineage-status", help="Inspect lineage state")
    lineage_parser.set_defaults(func=cmd_lineage_status)

    domain_parser = subparsers.add_parser("domain-status", help="Inspect domain state")
    domain_parser.set_defaults(func=cmd_domain_status)

    pressure_parser = subparsers.add_parser("pressure-status", help="Inspect pressure summary")
    pressure_parser.set_defaults(func=cmd_pressure_status)

    economy_parser = subparsers.add_parser("economy-status", help="Inspect economy summary")
    economy_parser.set_defaults(func=cmd_economy_status)

    stability_parser = subparsers.add_parser("stability-status", help="Inspect long-horizon stability summary")
    stability_parser.set_defaults(func=cmd_stability_status)

    safety_parser = subparsers.add_parser("safety-status", help="Inspect runtime safety and guardrail state")
    safety_parser.set_defaults(func=cmd_safety_status)

    long_run_parser = subparsers.add_parser("long-run-check", help="Run tiered long-run validation")
    long_run_parser.add_argument("--tier", choices=sorted(LONG_RUN_TIERS), default="bounded")
    long_run_parser.add_argument("--ticks", type=int, default=None)
    long_run_parser.add_argument("--seed", type=int, default=42)
    long_run_parser.set_defaults(func=cmd_long_run_check)

    build_release_parser = subparsers.add_parser("build-release", help="Build release zip")
    build_release_parser.set_defaults(func=cmd_build_release)

    validate_release_parser = subparsers.add_parser("validate-release", help="Validate release tree")
    validate_release_parser.set_defaults(func=cmd_validate_release)
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
    summary["boundary"] = validate_system_boundary(
        {
            "human": ["goal", "essence", "constraints", "acceptance"],
            "system": ["exploration", "implementation", "validation", "evolution", "expansion"],
        }
    )
    print(json.dumps(summary, ensure_ascii=True))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    runtime = build_runtime(args)
    reports = runtime.run(max_ticks=args.ticks)
    if reports:
        print(json.dumps(reports[-1], ensure_ascii=True))
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


def cmd_replay_check(args: argparse.Namespace) -> int:
    payload = replay_projection()
    print(json.dumps(payload, ensure_ascii=True))
    return 0 if payload.get("replay_ok") else 1


def cmd_status(args: argparse.Namespace) -> int:
    summary = status_projection()
    print(json.dumps(summary, ensure_ascii=True))
    return 0


def cmd_health(args: argparse.Namespace) -> int:
    payload = status_projection()
    ok = bool(payload.get("replay", {}).get("replay_ok")) if isinstance(payload.get("replay"), dict) else False
    print(json.dumps(payload, ensure_ascii=True))
    return 0 if ok else 1


def cmd_civilization_status(args: argparse.Namespace) -> int:
    print(json.dumps(civilization_projection(), ensure_ascii=True))
    return 0


def cmd_lineage_status(args: argparse.Namespace) -> int:
    print(json.dumps(lineage_projection(), ensure_ascii=True))
    return 0


def cmd_domain_status(args: argparse.Namespace) -> int:
    print(json.dumps(domain_projection(), ensure_ascii=True))
    return 0


def cmd_pressure_status(args: argparse.Namespace) -> int:
    print(json.dumps(pressure_projection(), ensure_ascii=True))
    return 0


def cmd_economy_status(args: argparse.Namespace) -> int:
    print(json.dumps(economy_projection(), ensure_ascii=True))
    return 0


def cmd_stability_status(args: argparse.Namespace) -> int:
    print(json.dumps(stability_projection(), ensure_ascii=True))
    return 0


def cmd_safety_status(args: argparse.Namespace) -> int:
    print(json.dumps(safety_projection(), ensure_ascii=True))
    return 0


def cmd_long_run_check(args: argparse.Namespace) -> int:
    ticks = int(args.ticks) if args.ticks is not None else int(LONG_RUN_TIERS[str(args.tier)]["ticks"])
    payload = validate_long_run(ticks=max(1, ticks), seed=int(args.seed), fail_open=True, tier=str(args.tier))
    print(json.dumps(payload, ensure_ascii=True))
    return 0 if payload.get("healthy") else 1


def _run_script(script_path: str) -> int:
    completed = subprocess.run(["bash", script_path], check=False)
    return int(completed.returncode)


def cmd_build_release(args: argparse.Namespace) -> int:
    return _run_script("scripts/build_release_zip.sh")


def cmd_validate_release(args: argparse.Namespace) -> int:
    return _run_script("scripts/validate_release_tree.sh")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
