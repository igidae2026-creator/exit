from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from genesis.contracts import QuestSlots


@dataclass(slots=True)
class LoopModel:
    tick: int
    phase: str
    quest_slots: QuestSlots
    bindings: Mapping[str, Any]
    quota: Mapping[str, Any]

