from __future__ import annotations

from typing import Any, Mapping, Sequence

from runtime.hysteresis import bounded_step


def _prev_workers(history: Sequence[Mapping[str, Any]]) -> int:
    for row in reversed(list(history)):
        if "workers" in row:
            return max(1, int(row.get("workers", 1)))
        budgets = row.get("budgets", {}) if isinstance(row.get("budgets"), Mapping) else {}
        if "effective_workers" in budgets:
            return max(1, int(budgets.get("effective_workers", 1)))
    return 0


def recover_budgets(
    budgets: Mapping[str, float | int],
    guard: Mapping[str, Any],
    history: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, float | int]:
    history = list(history or [])
    guard = dict(guard or {})
    out = dict(budgets)
    current_workers = max(1, int(out.get("effective_workers", out.get("workers", 1))))
    prev_workers = _prev_workers(history) or current_workers

    target_workers = current_workers
    if current_workers <= 2:
        target_workers = max(3, prev_workers)
    elif guard.get("downshift_workers"):
        target_workers = max(2, current_workers)
    elif not guard.get("repair_storm"):
        target_workers = max(current_workers + 1, min(prev_workers + 1, current_workers + 2))

    next_workers = int(round(bounded_step(float(current_workers), float(target_workers), max_delta=2.0, lo=2.0, hi=max(4.0, float(target_workers)))))
    if guard.get("repair_storm") and current_workers > 2:
        next_workers = max(2, min(current_workers, next_workers))
    out["worker_budget"] = next_workers
    out["workers"] = next_workers
    out["effective_workers"] = next_workers

    total_budget = float(next_workers * 10)
    out["mutation_budget"] = round(max(8.0, min(80.0, float(out.get("mutation_budget", 8.0)))), 4)
    out["repair_budget"] = round(max(0.0, min(60.0, float(out.get("repair_budget", 0.0)))), 4)
    out["replay_budget"] = round(max(4.0, min(80.0, float(out.get("replay_budget", total_budget * 0.22)))), 4)
    out["archive_budget"] = round(max(4.0, min(60.0, float(out.get("archive_budget", total_budget * 0.18)))), 4)
    out["domain_budget"] = round(max(4.0, min(60.0, float(out.get("domain_budget", total_budget * 0.16)))), 4)
    return out
