from __future__ import annotations

from typing import Any

from genesis.replay import replay_state
from runtime.civilization_memory import civilization_state
from runtime.lineage_ecology import assess_lineages
from runtime.runtime_safety import runtime_safety


def pressure_summary() -> dict[str, Any]:
    state = replay_state()
    return dict(state.get("pressure_state", {}))


def economy_summary() -> dict[str, Any]:
    state = replay_state()
    summary = dict(state.get("resource_allocation", {}))
    if not summary:
        summary = dict(state.get("exploration_economy_state", {}))
    return summary


def lineage_summary() -> dict[str, Any]:
    state = replay_state()
    lineage_state = state.get("lineage_state", {}) if isinstance(state.get("lineage_state"), dict) else {}
    rows = [{"lineage_id": key, "count": value} for key, value in dict(lineage_state.get("lineages", {})).items()]
    out = assess_lineages(rows or [{"lineage_id": "default"}], diversity_floor=2)
    out["surviving_lineages"] = int(lineage_state.get("surviving_lineages", out["surviving_lineages"]))
    out["lineage_concentration"] = float(lineage_state.get("lineage_concentration", out["lineage_concentration"]))
    return out


def domain_summary() -> dict[str, Any]:
    civ = civilization_state()
    domains = dict(civ.get("domain_distribution", {}))
    return {
        "active_domains": sorted(domains),
        "domain_distribution": domains,
        "domain_count": len(domains),
    }


def civilization_summary() -> dict[str, Any]:
    return civilization_state()


def replay_summary() -> dict[str, Any]:
    state = replay_state()
    return {
        "tick": int(state.get("tick", 0)),
        "events": int(state.get("events", 0)),
        "metrics": int(state.get("metrics", 0)),
        "artifacts": int(state.get("artifacts", 0)),
        "replay_ok": bool(state),
    }


def runtime_summary() -> dict[str, Any]:
    return {
        "replay": replay_summary(),
        "civilization": civilization_summary(),
        "lineages": lineage_summary(),
        "domains": domain_summary(),
        "pressure": pressure_summary(),
        "economy": economy_summary(),
        "safety": runtime_safety(),
    }


__all__ = [
    "civilization_summary",
    "domain_summary",
    "economy_summary",
    "lineage_summary",
    "pressure_summary",
    "replay_summary",
    "runtime_summary",
]
