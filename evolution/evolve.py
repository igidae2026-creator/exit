from __future__ import annotations

from typing import Any

from runtime.economy_controller import resource_allocation


def policy_evolution_hook(replay_state: object, pressures: dict[str, float]) -> dict[str, Any]:
    novelty = float(pressures.get("novelty_pressure", 0.0))
    repair = float(pressures.get("repair_pressure", 0.0))
    efficiency = float(pressures.get("efficiency_pressure", 0.0))
    return {
        "selection_bias": "novelty" if novelty >= efficiency else "efficiency",
        "mutation_scale": round(0.08 + (0.20 * max(novelty, repair)), 6),
        "safe_mode_bias": repair >= 0.75,
        "policy_version": len(getattr(replay_state, "policies", []) or []) + 1,
    }


def quota_allocator_hook(
    *,
    total_budget: float,
    collapse_state: dict[str, Any],
    exploration_ratio: float,
    mutation_pressure: float,
) -> dict[str, float]:
    return resource_allocation(
        total_budget,
        collapse_state,
        exploration_ratio,
        mutation_pressure,
        minimums={"recovery": 0.10},
    )


def archive_pressure_hook(replay_state: object, *, archive_limit: int = 5000) -> dict[str, Any]:
    artifact_count = len(getattr(replay_state, "artifacts", {}) or {})
    archive_pressure = min(1.0, artifact_count / max(1, archive_limit))
    return {
        "artifact_count": artifact_count,
        "archive_pressure": round(archive_pressure, 6),
        "should_prune": artifact_count > archive_limit,
    }


def choose_parent_ids(replay_state: object, *, limit: int = 2) -> list[str]:
    artifacts = getattr(replay_state, "artifacts", {}) or {}
    ranked = sorted(
        artifacts.values(),
        key=lambda row: (float(row.get("score") or 0.0), int(row.get("tick") or 0)),
        reverse=True,
    )
    parent_ids: list[str] = []
    for row in ranked:
        artifact_id = str(row.get("artifact_id") or "")
        if artifact_id:
            parent_ids.append(artifact_id)
        if len(parent_ids) >= limit:
            break
    return parent_ids


def signal(replay_state: object) -> dict[str, Any]:
    return {
        "tick": int(getattr(replay_state, "tick", 0) or 0) + 1,
        "artifact_count": len(getattr(replay_state, "artifacts", {}) or {}),
        "best_score": float(getattr(replay_state, "best_score", 0.0) or 0.0),
    }


def archive(replay_state: object) -> dict[str, Any]:
    return archive_pressure_hook(replay_state)


def selection(replay_state: object) -> dict[str, Any]:
    return {"parent_ids": choose_parent_ids(replay_state)}


def mutation(policy: dict[str, Any], pressures: dict[str, float]) -> dict[str, Any]:
    return {
        "selection_bias": policy.get("selection_bias", "novelty"),
        "mutation_scale": policy.get("mutation_scale", 0.1),
        "pressure_bias": max(pressures.get("novelty_pressure", 0.0), pressures.get("repair_pressure", 0.0)),
    }
