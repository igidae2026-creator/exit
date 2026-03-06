from metaos.runtime.hysteresis import bounded_step, clamp01, cooldown, smooth


def test_hysteresis_helpers_are_bounded() -> None:
    assert clamp01(1.4) == 1.0
    assert round(smooth(1.0, prev=0.0, alpha=0.2), 4) == 0.2
    assert round(bounded_step(0.1, 0.5, max_delta=0.08), 4) == 0.18
    assert cooldown(3, 2) is True
