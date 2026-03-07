from __future__ import annotations

from dataclasses import dataclass


CANONICAL_EXPLORATION_LOOP = (
    "signal",
    "generate",
    "evaluate",
    "select",
    "mutate",
    "archive",
    "repeat",
)

FAILURE_PROTOCOL_STATES = (
    "plateau",
    "exploration_collapse",
    "diversity_repair_failure",
    "repair_escalation",
    "invalid_state",
    "replay_restore",
)


@dataclass(frozen=True, slots=True)
class EcologyThresholds:
    minimum: int
    preferred: int


LINEAGE_ECOLOGY = EcologyThresholds(minimum=8, preferred=16)
DOMAIN_ECOLOGY = EcologyThresholds(minimum=4, preferred=8)
DOMINANCE_CAP = 0.35
DOMINANCE_EMERGENCY = 0.45


def failure_protocol_state(
    *,
    replay_ok: bool,
    repair_pressure: float,
    surviving_lineages: int,
    active_domains: int,
    dominance_index: float,
) -> str:
    if not replay_ok:
        return "replay_restore"
    if surviving_lineages <= 0 or active_domains <= 0:
        return "invalid_state"
    if repair_pressure >= 0.9:
        return "repair_escalation"
    if dominance_index > DOMINANCE_EMERGENCY:
        return "diversity_repair_failure"
    if surviving_lineages < LINEAGE_ECOLOGY.minimum or active_domains < DOMAIN_ECOLOGY.minimum:
        return "exploration_collapse"
    if repair_pressure >= 0.75:
        return "plateau"
    return "plateau"


__all__ = [
    "CANONICAL_EXPLORATION_LOOP",
    "DOMAIN_ECOLOGY",
    "DOMINANCE_CAP",
    "DOMINANCE_EMERGENCY",
    "FAILURE_PROTOCOL_STATES",
    "LINEAGE_ECOLOGY",
    "EcologyThresholds",
    "failure_protocol_state",
]
