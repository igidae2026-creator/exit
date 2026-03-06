from kernel.recovery import rollback
from kernel.supervisor import guarded_step


def test_recovery_flow_uses_fallback_without_crashing() -> None:
    state = {"tick": 1}

    def fail(_: dict[str, int]) -> dict[str, int]:
        raise RuntimeError("boom")

    out = guarded_step(fail, state, on_fail=lambda restored: rollback(restored, {"tick": 0}))
    assert out == {"tick": 0}

