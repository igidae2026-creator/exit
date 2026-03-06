from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ManagerState:
    tick: int = 0
    runtime_slots: dict[str, int] = field(default_factory=dict)
    exploration_budgets: dict[str, float] = field(default_factory=dict)
    selected_experiments: list[str] = field(default_factory=list)


__all__ = ["ManagerState"]
