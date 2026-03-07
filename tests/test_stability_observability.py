from runtime.observability import safety_status, stability_status


def test_stability_observability_surfaces_are_present() -> None:
    stability = stability_status()
    safety = safety_status()
    assert "stability_score" in stability
    assert "guardrail_actions" in safety
