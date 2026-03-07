from __future__ import annotations

from runtime.core_loop import DEFAULT_STAGE_ORDER, RuntimeLoop
from runtime.genesis_ceiling import CANONICAL_EXPLORATION_LOOP, failure_protocol_state


def test_core_loop_defaults_to_canonical_genesis_order() -> None:
    assert tuple(DEFAULT_STAGE_ORDER) == CANONICAL_EXPLORATION_LOOP


def test_core_loop_accepts_legacy_alias_handlers() -> None:
    seen: list[str] = []
    loop = RuntimeLoop(
        {
            "signal": lambda _ctx: seen.append("signal"),
            "strategy": lambda _ctx: seen.append("generate"),
            "artifact": lambda _ctx: seen.append("evaluate"),
            "decision": lambda _ctx: seen.append("select"),
            "mutation": lambda _ctx: seen.append("mutate"),
            "log": lambda _ctx: seen.append("archive"),
        }
    )

    loop.step()

    assert seen == ["signal", "generate", "evaluate", "select", "mutate", "archive"]


def test_failure_protocol_state_uses_ceiling_thresholds() -> None:
    assert (
        failure_protocol_state(
            replay_ok=True,
            repair_pressure=0.1,
            surviving_lineages=7,
            active_domains=4,
            dominance_index=0.2,
        )
        == "exploration_collapse"
    )
    assert (
        failure_protocol_state(
            replay_ok=True,
            repair_pressure=0.1,
            surviving_lineages=16,
            active_domains=8,
            dominance_index=0.46,
        )
        == "diversity_repair"
    )
