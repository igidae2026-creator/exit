from __future__ import annotations

from typing import Any, Mapping, Sequence

from genesis.contracts import QuotaFrame
from metaos.runtime.quota_allocator import allocate


def quota_frame(
    pressure: Mapping[str, float],
    workers: int,
    market_state: Mapping[str, float] | None = None,
    *,
    tick: int,
    guard: Mapping[str, Any] | None = None,
    history: Sequence[Mapping[str, Any]] | None = None,
) -> QuotaFrame:
    budgets = allocate(pressure, workers, market_state, guard=guard, history=history)
    return QuotaFrame(tick=int(tick), workers=int(budgets.get("effective_workers", workers)), budgets=budgets)

