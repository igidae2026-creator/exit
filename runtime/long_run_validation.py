from __future__ import annotations

import os
from typing import Any

from genesis.replay import replay_state
from runtime.soak_runner import run_soak
from runtime.civilization_memory import civilization_state
from runtime.observability import domain_summary, lineage_summary
from runtime.runtime_safety import runtime_safety


def run_long_run_validation(*, ticks: int = 120, seed: int = 42, fail_open: bool = True) -> dict[str, Any]:
    os.environ.setdefault("METAOS_SOAK_FAST", "1")
    soak_ticks, summary = run_soak(ticks=ticks, seed=seed, fail_open=fail_open)
    replay = replay_state()
    civ = civilization_state()
    lineages = lineage_summary()
    domains = domain_summary()
    safety = runtime_safety()
    return {
        "ticks": len(soak_ticks),
        "summary": summary,
        "replay_ok": bool(replay),
        "civilization_state": civ,
        "lineages": lineages,
        "domains": domains,
        "runtime_safety": safety,
        "memory_growth": float(civ.get("memory_growth", 0.0)),
        "surviving_lineages": int(lineages.get("surviving_lineages", 0)),
        "domain_count": int(domains.get("domain_count", 0)),
        "healthy": bool(replay) and float(civ.get("memory_growth", 0.0)) > 0.0,
    }


__all__ = ["run_long_run_validation"]
