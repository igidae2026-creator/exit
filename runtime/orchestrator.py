from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.kernel_adapter import DEFAULT_RUNTIME_ROOT, KernelAdapter
from runtime.profiles import active_profile, runtime_profile
from runtime.replay_state import replay_state
from runtime.supervisor import Supervisor


@dataclass(slots=True)
class OrchestratorConfig:
    tick_seconds: float = 0.05
    max_ticks: int | None = None
    profile: str = "production"
    runtime_profile: str = "smoke"
    data_dir: Path = DEFAULT_RUNTIME_ROOT / "data"
    artifact_store_dir: Path = DEFAULT_RUNTIME_ROOT / "artifact_store"
    state_dir: Path = DEFAULT_RUNTIME_ROOT / "state"
    archive_dir: Path = DEFAULT_RUNTIME_ROOT / "archive"
    canonical_domain: str = "code_domain"

    @classmethod
    def from_env(cls) -> "OrchestratorConfig":
        runtime_root = Path(os.getenv("METAOS_RUNTIME_ROOT", str(DEFAULT_RUNTIME_ROOT)))
        profile = active_profile(os.getenv("METAOS_PROFILE"))
        runtime_validation_profile = runtime_profile(os.getenv("METAOS_RUNTIME_PROFILE"))
        return cls(
            tick_seconds=_env_float("METAOS_TICK_SECONDS", profile.tick_seconds),
            max_ticks=_env_int_or_none("METAOS_MAX_TICKS", profile.default_ticks),
            profile=profile.name,
            runtime_profile=runtime_validation_profile.name,
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
        limit = self._resolved_limit(max_ticks=max_ticks)
        reports: list[dict[str, Any]] = []
        tick_count = 0
        while limit is None or tick_count < limit:
            state = replay_state(
                self.config.data_dir,
                state_dir=self.config.state_dir,
                archive_dir=self.config.archive_dir,
            )
            report = self.supervisor.run_cycle(state)
            reports.append(report)
            tick_count += 1
            print(json.dumps(report, ensure_ascii=True, separators=(",", ":")), flush=True)
            if self.config.tick_seconds > 0:
                time.sleep(self.config.tick_seconds)
        return reports

    def _resolved_limit(self, *, max_ticks: int | None) -> int | None:
        if max_ticks is not None:
            return None if int(max_ticks) <= 0 else int(max_ticks)
        if self.config.max_ticks is not None:
            return None if int(self.config.max_ticks) <= 0 else int(self.config.max_ticks)
        profile = active_profile(self.config.profile)
        if profile.default_ticks is not None:
            return int(profile.default_ticks)
        return None

    def validate(self) -> dict[str, Any]:
        validation_profile = runtime_profile(self.config.runtime_profile)
        summary = self.supervisor.validate()
        summary["runtime_profile"] = validation_profile.name
        summary["runtime_target_ticks"] = validation_profile.target_ticks
        summary["runtime_target_lineages"] = validation_profile.target_surviving_lineages
        summary["runtime_target_domains"] = validation_profile.target_active_domains
        summary["bounded"] = self.config.max_ticks is not None
        return summary

    def replay(self) -> dict[str, Any]:
        state = replay_state(
            self.config.data_dir,
            state_dir=self.config.state_dir,
            archive_dir=self.config.archive_dir,
        )
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


def _env_int_or_none(name: str, default: int | None) -> int | None:
    raw = os.getenv(name)
    if raw is None:
        return default
    text = raw.strip().lower()
    if text in {"", "none", "null", "unbounded", "infinite", "continuous"}:
        return None
    try:
        value = int(raw)
    except ValueError:
        return default
    return None if value <= 0 else value


def run() -> None:
    Orchestrator().run()


if __name__ == "__main__":
    run()
