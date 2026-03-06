from __future__ import annotations

from typing import Any

from artifact.lineage import dominant_lineage, lineage_concentration
from evolution.quota_allocator import allocate_quota
from runtime.economy_controller import resource_allocation


def policy_evolution_hook(replay_state: object, pressures: dict[str, float]) -> dict[str, Any]:
    novelty = float(pressures.get("novelty_pressure", 0.0))
    repair = float(pressures.get("repair_pressure", 0.0))
    diversity = float(pressures.get("diversity_pressure", 0.0))
    transfer = float(pressures.get("transfer_pressure", 0.0))
    policies = list(getattr(replay_state, "policies", []) or [])
    return {
        "selection_bias": "diversity" if diversity >= novelty else "novelty",
        "mutation_scale": round(0.06 + (0.18 * max(novelty, repair, transfer)), 6),
        "safe_mode_bias": repair >= 0.72,
        "transfer_bias": round(0.20 + (0.45 * transfer), 6),
        "retention_floor": round(0.30 + (0.20 * diversity), 6),
        "policy_version": len(policies) + 1,
    }


def quota_allocator_hook(*, total_budget: float, collapse_state: dict[str, Any], exploration_ratio: float, mutation_pressure: float) -> dict[str, float]:
    return resource_allocation(total_budget, collapse_state, exploration_ratio, mutation_pressure, minimums={"repair_budget": 0.10})


def archive_pressure_hook(replay_state: object, *, archive_limit: int = 5000) -> dict[str, Any]:
    archive = getattr(replay_state, "archive", {}) or {}
    artifact_count = len(getattr(replay_state, "artifacts", {}) or {})
    archive_rows = sum(len(rows) for rows in archive.values())
    archive_pressure = min(1.0, archive_rows / max(1, archive_limit))
    return {
        "artifact_count": artifact_count,
        "archive_rows": archive_rows,
        "archive_pressure": round(archive_pressure, 6),
        "should_prune": archive_rows > archive_limit,
    }


def choose_parent_ids(replay_state: object, *, limit: int = 3) -> list[str]:
    artifacts = getattr(replay_state, "artifacts", {}) or {}
    ranked = sorted(artifacts.values(), key=lambda row: (float(row.get("score") or 0.0), int(row.get("tick") or 0)), reverse=True)
    return [str(row.get("artifact_id")) for row in ranked[:limit] if row.get("artifact_id")]


def signal(replay_state: object) -> dict[str, Any]:
    return {
        "tick": int(getattr(replay_state, "tick", 0) or 0) + 1,
        "artifact_count": len(getattr(replay_state, "artifacts", {}) or {}),
        "best_score": float(getattr(replay_state, "best_score", 0.0) or 0.0),
        "lineage_concentration": float(getattr(replay_state, "lineage_concentration", lambda: 0.0)() if hasattr(replay_state, "lineage_concentration") else 0.0),
    }


def archive(replay_state: object) -> dict[str, Any]:
    return archive_pressure_hook(replay_state)


def selection(replay_state: object) -> dict[str, Any]:
    parent_ids = choose_parent_ids(replay_state)
    dominant, count = dominant_lineage(getattr(replay_state, "data_dir", "data") if hasattr(replay_state, "data_dir") else "data")
    return {"parent_ids": parent_ids, "dominant_lineage": dominant, "dominant_count": count, "lineage_concentration": lineage_concentration(getattr(replay_state, "data_dir", "data") if hasattr(replay_state, "data_dir") else "data")}


def mutation(policy: dict[str, Any], pressures: dict[str, float]) -> dict[str, Any]:
    budget_hint = allocate_quota(pressures)
    return {
        "selection_bias": policy.get("selection_bias", "novelty"),
        "mutation_scale": policy.get("mutation_scale", 0.1),
        "pressure_bias": max(pressures.get("novelty_pressure", 0.0), pressures.get("repair_pressure", 0.0), pressures.get("transfer_pressure", 0.0)),
        "budget_hint": budget_hint,
    }
