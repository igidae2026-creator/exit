from __future__ import annotations

from typing import Any, Mapping

from metaos.runtime.evolve_exploration_strategy import evolve_strategy


def propose_mutation(
    current: Mapping[str, Any] | None,
    pressure: Mapping[str, float],
    market_state: Mapping[str, float],
) -> dict[str, Any]:
    return evolve_strategy(current=current, pressure=pressure, market_state=market_state)

