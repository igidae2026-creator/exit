from __future__ import annotations

from typing import Any, Mapping, Sequence

from metaos.runtime.civilization_selection import civilization_select


def select_artifact(
    candidates: Sequence[Mapping[str, Any]],
    pressure: Mapping[str, float],
    market_state: Mapping[str, float],
    ecology: Mapping[str, float],
) -> dict[str, Any]:
    return civilization_select(candidates, pressure, market_state, ecology)

