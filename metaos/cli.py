from __future__ import annotations

import argparse
import json
from typing import Sequence

from core.kernel_adapter import KernelAdapter
from core.replay import replay_state
from core.supervisor import Supervisor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="metaos", description="METAOS Civilization MVP CLI")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--artifact-dir", default="artifact_store")
    parser.add_argument("--state-dir", default="state")
    parser.add_argument("--domain", default="code_domain")

    subparsers = parser.add_subparsers(dest="command", required=False)

    validate_parser = subparsers.add_parser("validate", help="Validate runtime wiring")
    validate_parser.set_defaults(func=cmd_validate)

    run_once_parser = subparsers.add_parser("run-once", help="Run one or more Civilization MVP cycles")
    run_once_parser.add_argument("--ticks", type=int, default=1)
    run_once_parser.set_defaults(func=cmd_run_once)

    replay_parser = subparsers.add_parser("replay", help="Replay append-only state")
    replay_parser.set_defaults(func=cmd_replay)
    return parser


def build_runtime(args: argparse.Namespace) -> tuple[KernelAdapter, Supervisor]:
    adapter = KernelAdapter(
        data_dir=args.data_dir,
        artifact_dir=args.artifact_dir,
        state_dir=args.state_dir,
        domain_name=args.domain,
    )
    return adapter, Supervisor(adapter)


def cmd_validate(args: argparse.Namespace) -> int:
    adapter, supervisor = build_runtime(args)
    try:
        summary = supervisor.validate()
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=True))
        return 2
    print(json.dumps(summary, ensure_ascii=True))
    return 0


def cmd_run_once(args: argparse.Namespace) -> int:
    adapter, supervisor = build_runtime(args)
    last_report: dict[str, object] = {}
    for _ in range(max(1, args.ticks)):
        state = replay_state(args.data_dir)
        last_report = supervisor.run_cycle(state)
    print(json.dumps(last_report, ensure_ascii=True))
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    state = replay_state(args.data_dir)
    print(
        json.dumps(
            {
                "tick": state.tick,
                "best_score": state.best_score,
                "artifacts": len(state.artifacts),
                "artifacts_by_kind": state.artifacts_by_kind,
                "active_quest": state.active_quest,
                "supervisor_mode": state.supervisor_mode,
                "plateau_streak": state.plateau_streak,
            },
            ensure_ascii=True,
        )
    )
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
