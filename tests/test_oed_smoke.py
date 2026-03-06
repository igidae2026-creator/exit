from metaos.runtime.oed_orchestrator import step


def test_oed_step() -> None:
    state = step(
        metrics={"score": 0.72, "novelty": 0.31, "diversity": 0.42, "cost": 0.18, "fail_rate": 0.03},
        policy=None,
        workers=8,
        domain="default",
        parent=None,
    )
    assert "quest" in state
    assert "policy" in state
    assert state["workers"] >= 1
    assert "pressure" in state
