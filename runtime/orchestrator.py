from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.kernel_adapter import DEFAULT_RUNTIME_ROOT, KernelAdapter
from runtime.replay_state import replay_state
from runtime.supervisor import Supervisor
from runtime.profiles import active_profile


@dataclass(slots=True)
class OrchestratorConfig:
    tick_seconds: float = 0.05
    max_ticks: int | None = None
    profile: str = "run"
    data_dir: Path = DEFAULT_RUNTIME_ROOT / "data"
    artifact_store_dir: Path = DEFAULT_RUNTIME_ROOT / "artifact_store"
    state_dir: Path = DEFAULT_RUNTIME_ROOT / "state"
    archive_dir: Path = DEFAULT_RUNTIME_ROOT / "archive"
    canonical_domain: str = "code_domain"

    @classmethod
    def from_env(cls) -> "OrchestratorConfig":
        runtime_root = Path(os.getenv("METAOS_RUNTIME_ROOT", str(DEFAULT_RUNTIME_ROOT)))
        profile = active_profile(os.getenv("METAOS_PROFILE"))
        return cls(
            tick_seconds=_env_float("METAOS_TICK_SECONDS", profile.tick_seconds),
            max_ticks=_env_int_or_none("METAOS_MAX_TICKS", profile.default_ticks),
            profile=profile.name,
            data_dir=Path(os.getenv("METAOS_DATA_DIR", str(runtime_root / "data"))),
            artifact_store_dir=Path(os.getenv("METAOS_ARTIFACT_STORE", str(runtime_root / "artifact_store"))),
            state_dir=Path(os.getenv("METAOS_STATE_DIR", str(runtime_root / "state"))),
            archive_dir=Path(os.getenv("METAOS_ARCHIVE_DIR", str(runtime_root / "archive"))),
            canonical_domain=os.getenv("METAOS_CANONICAL_DOMAIN", "code_domain"),
        )


class Orchestrator:
    def __init__(self, config: OrchestratorConfig | None = None) -> None:
        self.config = config or OrchestratorConfig.from_env()
        self.adapter = KernelAdapter(
            data_dir=self.config.data_dir,
            artifact_dir=self.config.artifact_store_dir,
            state_dir=self.config.state_dir,
            archive_dir=self.config.archive_dir,
            domain_name=self.config.canonical_domain,
        )
        self.supervisor = Supervisor(self.adapter)

    def run(self, *, max_ticks: int | None = None) -> list[dict[str, Any]]:
        limit = self.config.max_ticks if max_ticks is None else max_ticks
        reports: list[dict[str, Any]] = []
        if limit is None:
            while True:
                state = replay_state(self.config.data_dir, state_dir=self.config.state_dir, archive_dir=self.config.archive_dir)
                report = self.supervisor.run_cycle(state)
                reports.append(report)
                print(json.dumps(report, ensure_ascii=True, separators=(",", ":")), flush=True)
                if self.config.tick_seconds > 0:
                    time.sleep(self.config.tick_seconds)
            return reports
        if limit <= 0:
            limit = 1
        for _ in range(limit):
            state = replay_state(self.config.data_dir, state_dir=self.config.state_dir, archive_dir=self.config.archive_dir)
            report = self.supervisor.run_cycle(state)
            reports.append(report)
            print(json.dumps(report, ensure_ascii=True, separators=(",", ":")), flush=True)
            if self.config.tick_seconds > 0:
                time.sleep(self.config.tick_seconds)
        return reports

    def validate(self) -> dict[str, Any]:
        return self.supervisor.validate()

    def replay(self) -> dict[str, Any]:
        state = replay_state(self.config.data_dir, state_dir=self.config.state_dir, archive_dir=self.config.archive_dir)
        return {
            "tick": state.tick,
            "best_score": state.best_score,
            "artifacts": len(state.artifacts),
            "artifacts_by_kind": state.artifacts_by_kind,
            "active_quest": state.active_quest,
            "quest_portfolio": state.quest_portfolio,
            "supervisor_mode": state.supervisor_mode,
            "plateau_streak": state.plateau_streak,
            "domains": state.domain_counts,
            "lineages": state.lineages,
        }


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def run() -> None:
    Orchestrator().run()


if __name__ == "__main__":
    run()


def _env_int_or_none(name: str, default: int | None) -> int | None:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default
